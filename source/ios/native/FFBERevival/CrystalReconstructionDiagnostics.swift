import Foundation
import UIKit

@MainActor enum CrystalReconstructionDiagnostics {
    private struct Failure: Error { let message: String }
    static func run(_ controller: CrystalReconstructionController) async -> String {
        var report: [String: Any] = [:]
        do {
            func require(_ value: Bool,_ message: String) throws { if !value { throw Failure(message: message) } }
            try require(controller.ready,"Original assets did not load")
            let folder = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation/reconstruction",isDirectory: true)
            try FileManager.default.createDirectory(at: folder,withIntermediateDirectories: true)
            for appearance in CrystalAppearance.allCases {
                controller.appearance = appearance; controller.inspect()
                _ = controller.snapshot()
                let image = controller.snapshot()
                try require(image.size.width>0 && image.size.height>0,"Missing rendered appearance")
                try image.pngData()?.write(to: folder.appendingPathComponent("reconstructed-"+appearance.rawValue.lowercased()+".png"),options: .atomic)
            }
            controller.appearance = .blue; controller.inspect()
            let referenceCount = controller.nodeCount
            controller.baseVisible = false; try require(controller.layerVisibility["base"] == false,"Base toggle failed"); controller.baseVisible = true
            controller.glossVisible = false; try require(controller.layerVisibility["gloss"] == false,"Gloss toggle failed"); controller.glossVisible = true
            controller.highlightsVisible = false; try require(controller.layerVisibility["highlights"] == false,"Highlight toggle failed"); controller.highlightsVisible = true
            controller.glowVisible = false; try require(controller.layerVisibility["glow"] == false,"Glow toggle failed"); controller.glowVisible = true
            controller.particlesVisible = false; try require(controller.layerVisibility["particles"] == false,"Particle toggle failed"); controller.particlesVisible = true
            controller.partialVisible = true; try require(controller.layerVisibility["partial"] == true,"Partial inspection failed"); controller.partialVisible = false
            controller.alternateModels = true; try require(controller.ready,"Alternate geometry failed"); controller.alternateModels = false
            controller.play()
            try await Task.sleep(nanoseconds: 300_000_000)
            controller.pause(); let paused = controller.clock.time
            try await Task.sleep(nanoseconds: 100_000_000)
            try require(controller.clock.state == .paused && controller.clock.time == paused && !controller.isTicking,"Pause did not freeze timeline")
            controller.play(); try await Task.sleep(nanoseconds: 100_000_000); controller.suspend()
            try require(controller.clock.state == .paused && !controller.isTicking,"Inactive playback did not pause")
            controller.stop(); try require(controller.clock.state == .stopped && !controller.isTicking,"Stop failed")
            // Drain temporary UIImage/GPU readback buffers before measuring repeats.
            // A synchronous batch without pools measures cold snapshot retention,
            // rather than the steady playback working set.
            let cold = CrystalInspection.residentBytes()
            for _ in 0..<6 {
                autoreleasepool {
                    controller.restart(); controller.seek(2.95); _ = controller.snapshot(); controller.stop()
                }
            }
            try await Task.sleep(nanoseconds: 150_000_000)
            let before = CrystalInspection.residentBytes()
            for _ in 0..<24 {
                autoreleasepool {
                    controller.restart(); controller.seek(2.95); _ = controller.snapshot(); controller.stop()
                }
                try require(controller.nodeCount == referenceCount && !controller.isTicking,"Repeated playback grew scene graph")
            }
            try await Task.sleep(nanoseconds: 150_000_000)
            let afterSnapshots = CrystalInspection.residentBytes()
            for _ in 0..<24 {
                controller.restart()
                try await Task.sleep(nanoseconds: 60_000_000)
                controller.stop()
                try require(controller.nodeCount == referenceCount && !controller.isTicking,"Live repeat grew scene graph")
            }
            try await Task.sleep(nanoseconds: 150_000_000)
            let after = CrystalInspection.residentBytes()
            var completed = 0
            controller.onCompletion = { if case .finished = $0 { completed += 1 } }
            let start = ProcessInfo.processInfo.systemUptime
            let callbacks = controller.callbackCount
            controller.restart()
            for _ in 0..<120 {
                if controller.clock.state == .finished { break }
                try await Task.sleep(nanoseconds: 100_000_000)
            }
            let elapsed = ProcessInfo.processInfo.systemUptime-start
            let measured = controller.callbackCount-callbacks
            try require(controller.clock.state == .finished && completed == 1 && !controller.isTicking,"End/reveal callback failed")
            let intervals = controller.frameIntervals.sorted()
            let median = intervals.isEmpty ? 0 : intervals[intervals.count/2]*1000
            let p95 = intervals.isEmpty ? 0 : intervals[min(intervals.count-1,Int(Double(intervals.count)*0.95))]*1000
            controller.stop(); try require(completed == 1,"Duplicate completion")
            controller.onCompletion = nil
            controller.seek(0.4); try controller.snapshot().pngData()?.write(to: folder.appendingPathComponent("reconstructed-arrival.png"),options: .atomic)
            controller.seek(2.95); try controller.snapshot().pngData()?.write(to: folder.appendingPathComponent("reconstructed-opening.png"),options: .atomic)
            let missing = CrystalReconstructionController(); missing.load(directory: folder.appendingPathComponent("missing"))
            try require(!missing.ready && !missing.isTicking,"Missing content accepted")
            let corruptRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
            defer { try? FileManager.default.removeItem(at: corruptRoot) }
            guard let original = CrystalReconstructionController.resourceDirectory else { throw Failure(message: "No source bundle") }
            try FileManager.default.copyItem(at: original,to: corruptRoot)
            try Data("bad".utf8).write(to: corruptRoot.appendingPathComponent("model001.json"))
            let corrupt = CrystalReconstructionController(); corrupt.load(directory: corruptRoot)
            try require(!corrupt.ready,"Corrupt content accepted")
            weak var released: CrystalReconstructionController?
            autoreleasepool {
                var temporary: CrystalReconstructionController? = CrystalReconstructionController()
                temporary?.load(); temporary?.play(); temporary?.stop(); released = temporary; temporary = nil
            }
            try require(released == nil,"Display-link ownership retained controller")
            controller.inspect()
            report = ["status":"passed","original_animation_recovered":false,"reconstruction":true,
                      "appearances":["blue","gold","rainbow"],"layer_toggles":true,"alternate_models":true,
                      "pause_froze_timeline":true,"stop_restart":true,"inactive_pause_handler":true,
                      "missing_and_corrupt_rejected":true,"completion_exactly_once":true,
                      "repeated_scene_graph_stable":true,"repeat_cycles":48,"snapshot_repeat_cycles":24,"live_restart_cycles":24,"controller_released":true,
                      "nodes":controller.nodeCount,"resident_cold":cold,"resident_before_cycles":before,
                      "resident_after_snapshot_cycles":afterSnapshots,"resident_after_cycles":after,
                      "frame_interval_median_ms":median,"frame_interval_p95_ms":p95,
                      "viewport_callbacks":measured,"elapsed_seconds":elapsed,"callbacks_per_second":Double(measured)/elapsed,
                      "resource_bytes":controller.resourceBytes,"normal_campaign_accessed":false,
                      "scope":"Viewport + isolated reconstruction; no backend. Handler tests are not physical Home/radio/reboot tests."]
            try JSONSerialization.data(withJSONObject: report,options: [.prettyPrinted,.sortedKeys]).write(to: folder.appendingPathComponent("report.json"),options: .atomic)
        } catch {
            controller.stop()
            let message = (error as? Failure)?.message ?? error.localizedDescription
            report = ["status":"failed","error":message]
            if let base = try? FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true) {
                let folder = base.appendingPathComponent("FFBERevival/validation/reconstruction")
                try? FileManager.default.createDirectory(at: folder,withIntermediateDirectories: true)
                try? JSONSerialization.data(withJSONObject: report,options: [.prettyPrinted,.sortedKeys]).write(to: folder.appendingPathComponent("report.json"))
            }
        }
        return String(describing: report)
    }
}
