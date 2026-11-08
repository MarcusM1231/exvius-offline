import Foundation
import UIKit

// Renderer-only diagnostics: no backend, currency, inventory or campaign access.
@MainActor enum CrystalEntranceDiagnostics {
    private struct Failure: Error { let message: String }
    static func run(_ c: CrystalReconstructionController) async -> String {
        var folder: URL?
        do {
            func require(_ ok: Bool,_ message: String) throws { if !ok { throw Failure(message: message) } }
            let root = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation/crystal-entrance")
            try FileManager.default.createDirectory(at: root,withIntermediateDirectories: true);folder = root
            try require(c.ready,"Original geometry unavailable")
            try require(c.entranceAssetsAvailable && c.touchPromptImage != nil,"Recovered TOUCH SCREEN/cloud bundle unavailable")
            let count = c.nodeCount, before = CrystalInspection.residentBytes()
            var results: [[String: Any]] = []
            for appearance in CrystalAppearance.allCases {
                c.onCompletion = nil;c.stop();c.appearance = appearance;c.startTapPresentation()
                var completions = 0;c.onCompletion = { outcome in if case .finished = outcome { completions += 1 } }
                try require(c.tapPhase == .fallingCrystals && !c.tapToBreak(),"Early tap skipped entrance")
                try await wait { (c.entranceElapsed ?? 0)>0.35 }
                try save(c,root,appearance,"begin")
                try await wait { (c.entranceElapsed ?? 0)>0.90 }
                let visible = c.visibleFallingCount
                try require(visible >= 2,"Multiple original-mesh crystals not visible")
                c.pause();let held = c.entranceElapsed, motion = c.productionMotionTime
                try await Task.sleep(nanoseconds: 150_000_000)
                try require(c.entranceElapsed == held && c.productionMotionTime == motion && !c.isTicking && !c.tapToBreak(),"Background pause advanced falling clock")
                c.resumeTapPresentation();try save(c,root,appearance,"mid-fall")
                try await wait { c.tapPhase == .arriving }
                try save(c,root,appearance,"arrival")
                try await wait { c.tapPhase == .waitingForTap }
                try require(c.visibleFallingCount == 0 && completions == 0,"Falling crystals leaked into idle or auto-opened")
                try save(c,root,appearance,"touch-screen")
                c.pause();let idle = c.productionMotionTime
                try await Task.sleep(nanoseconds: 100_000_000);try require(c.productionMotionTime == idle && !c.tapToBreak(),"Paused idle accepted tap")
                c.resumeTapPresentation();try await Task.sleep(nanoseconds: 600_000_000)
                try require(c.tapPhase == .waitingForTap && completions == 0,"Idle opened automatically")
                try require(c.tapToBreak(),"Valid tap rejected")
                for _ in 0..<30 {try require(!c.tapToBreak(),"Repeat tap opened twice")}
                try await Task.sleep(nanoseconds: 250_000_000);try save(c,root,appearance,"opening")
                try await wait { c.tapPhase == .finished }
                try require(completions == 1 && !c.isTicking,"Completion was not once-only")
                c.stop();try require(completions == 1 && c.visibleFallingCount == 0 && c.nodeCount == count,"Stop changed completion/scene graph")
                results.append(["appearance":appearance.rawValue,"visible_mid_fall":visible,"completion_count":completions,"nodes":c.nodeCount])
            }
            c.onCompletion = nil
            let warmBefore = CrystalInspection.residentBytes()
            for _ in 0..<40 {c.startTapPresentation();c.pause();c.resumeTapPresentation();c.stop()}
            try require(c.nodeCount == count && !c.isTicking,"Repeated entrance leaked nodes/display link")
            try await Task.sleep(nanoseconds: 100_000_000)
            let warmAfter = CrystalInspection.residentBytes()
            let missing = CrystalReconstructionController();missing.load(entranceDirectory: root.appendingPathComponent("absent"))
            try require(missing.ready && !missing.entranceAssetsAvailable && missing.touchPromptImage == nil,"Optional prompt did not fall back safely")
            missing.inspectTouchState();try require(missing.tapPhase == .waitingForTap,"Fallback prompt could not reach ready state");missing.stop()
            let corrupt = root.appendingPathComponent("corrupt-"+UUID().uuidString)
            if let original = CrystalEntranceResources.directory {
                try FileManager.default.copyItem(at: original,to: corrupt)
                try Data("corrupt".utf8).write(to: corrupt.appendingPathComponent("touchscreen.png"))
                missing.load(entranceDirectory: corrupt)
                try require(missing.ready && !missing.entranceAssetsAvailable,"Corrupt optional prompt accepted")
                try FileManager.default.removeItem(at: corrupt)
            }
            missing.load(directory: root.appendingPathComponent("absent-core"))
            var unavailable = 0;missing.onCompletion = { outcome in if case .unavailable = outcome {unavailable += 1} };missing.startTapPresentation()
            try require(!missing.ready && unavailable == 1,"Missing core did not report safe fallback")
            weak var released: CrystalReconstructionController?
            autoreleasepool { let temporary = CrystalReconstructionController();temporary.load();temporary.startTapPresentation();released = temporary }
            try require(released == nil,"Weak display-link target retained controller")
            let intervals = c.frameIntervals.sorted()
            let report: [String: Any] = ["status":"passed","appearances":results,"normal_campaign_accessed":false,
                "original_timeline_recovered":false,"prompt_lock_sha256":CrystalEntranceResources.lockHash,"recovered_prompt_loaded":true,"decorative_palette":["blue","gold","rainbow"],"reconstructed_count":CrystalEntranceTiming.count,
                "pause_resume":true,"early_and_repeat_taps_ignored":true,"indefinite_wait_gate":true,
                "missing_optional_safe_native_prompt":true,"missing_core_safe_fallback":true,"corrupt_optional_rejected":true,
                "repeat_cycles":40,"stable_nodes":true,"controller_released":true,
                "resident_before":before,"resident_after":CrystalInspection.residentBytes(),
                "resident_warm_before_cycles":warmBefore,"resident_warm_after_cycles":warmAfter,
                "frame_interval_median_ms":intervals.isEmpty ? 0 : intervals[intervals.count/2]*1000,
                "frame_interval_p95_ms":intervals.isEmpty ? 0 : intervals[min(intervals.count-1,Int(Double(intervals.count)*0.95))]*1000]
            try JSONSerialization.data(withJSONObject: report,options: [.prettyPrinted,.sortedKeys]).write(to: root.appendingPathComponent("report.json"),options: .atomic)
            c.appearance = .blue;c.inspectTouchState()
            return "Passed: falling entrance, original prompt, three appearances, tap/lifecycle/cleanup checks"
        } catch {
            c.onCompletion = nil;c.stop()
            if let folder {try? JSONSerialization.data(withJSONObject: ["status":"failed","error":String(describing:error),"normal_campaign_accessed":false],options: [.prettyPrinted]).write(to: folder.appendingPathComponent("report.json"))}
            return String(describing:error)
        }
    }
    private static func wait(_ condition: () -> Bool) async throws {
        for _ in 0..<500 {if condition() {return};try await Task.sleep(nanoseconds: 20_000_000)}
        throw Failure(message:"Timed out waiting for entrance state")
    }
    private static func save(_ c: CrystalReconstructionController,_ folder: URL,_ appearance: CrystalAppearance,_ stage: String) throws {
        try c.snapshot().pngData()?.write(to: folder.appendingPathComponent(appearance.rawValue.lowercased()+"-"+stage+".png"))
    }
}
