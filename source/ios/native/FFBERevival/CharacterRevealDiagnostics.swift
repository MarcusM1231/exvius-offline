import SwiftUI
import UIKit
import CryptoKit

// Isolated route. Physical execution requires the explicitly authorized falling-summon flag.
struct CharacterRevealDiagnostics: View {
    @StateObject private var model = SummonModel()
    @StateObject private var crystal = CrystalReconstructionController()
    @State private var character: CharacterRevealController?
    @State private var receipt: CommittedSummon?
    @State private var presenting = false
    @State private var coverDismissed = true
    @State private var returned: [Award] = []
    @State private var callbacks = 0
    @State private var status = "Preparing isolated Simulator diagnostic…"
    @State private var reliable = false
    @State private var showGrid = false
    var body: some View {
        VStack {
            Text("ISOLATED CHARACTER REVEAL · " + status).font(.caption2).padding(6).background(.purple)
            if showGrid { GlobalSummonResults(awards: returned,reliable: $reliable) {} }
            else { Spacer(); Text(status); Spacer() }
        }.foregroundStyle(.white).background(.black)
            .fullScreenCover(isPresented: $presenting,onDismiss: { coverDismissed = true }) {
                if let receipt {
                    CommittedSummonPresentation(receipt: receipt,complete: { awards in
                        callbacks += 1; returned = awards; presenting = false; showGrid = true
                    },crystalController: crystal,characterController: character).id(receipt.id)
                }
            }.task { await run() }
    }
    private static var isSimulator: Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }
    private struct Failure: Error { let text: String }
    @MainActor private func run() async {
        #if !targetEnvironment(simulator)
        guard ProcessInfo.processInfo.arguments.contains("--falling-summon-diagnostics") else {status = "Use explicitly authorized falling-summon diagnostics on a physical device";return}
        #endif
        var folder: URL?
        do {
            func require(_ condition: Bool,_ message: String) throws { if !condition { throw Failure(text: message) } }
            let base = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation/character-reveal")
            try FileManager.default.createDirectory(at: base,withIntermediateDirectories: true);folder = base
            let reload = ProcessInfo.processInfo.arguments.contains("--character-reveal-reload-check")
            var expected: [String: Any] = [:]
            let relative: String
            if reload {
                expected = try JSONSerialization.jsonObject(with: Data(contentsOf: base.appendingPathComponent("last-test.json"))) as? [String: Any] ?? [:]
                guard let r = expected["relative_root"] as? String,r.hasPrefix("run-"),UUID(uuidString: String(r.dropFirst(4))) != nil else { throw Failure(text: "Invalid isolated recovery marker") }
                relative = r
            } else { relative = "run-"+UUID().uuidString }
            let root = base.appendingPathComponent(relative);try FileManager.default.createDirectory(at: root,withIntermediateDirectories: true)
            let backend = CountedEmbeddedBackend(storage: root.appendingPathComponent("campaign"),journal: root.appendingPathComponent("counters.json"))
            await model.refresh(using: backend,identity: "character-diagnostic")
            try require(model.campaign != nil && !model.needsRefresh,"Isolated backend initialization failed")
            let save = root.appendingPathComponent("campaign/campaign.json")
            if reload {
                try require(model.results.map(\.instance_id) == expected["award_ids"] as? [String],"Cold recovery changed awards")
                try require(model.campaign?.currencies["lapis_free"] == expected["lapis"] as? Int && backend.requests == 0,"Cold recovery summoned/charged")
                let hash = try digest(save)
                try require(hash == expected["save_sha256"] as? String,"Cold recovery rewrote the save")
                returned = model.results;showGrid = true;status = "Cold recovery passed"
                try write(["status":"passed","summon_requests":0,"save_unchanged":true,"award_ids":returned.map(\.instance_id),"normal_campaign_accessed":false],base.appendingPathComponent("reload-report.json"));return
            }
            guard let banner = model.banners.first(where: { $0.id == "9100203" }),
                  let single = banner.offer_details.first(where: { $0.offer == "primary" }),
                  let multi = banner.offer_details.first(where: { $0.offer == "secondary" }) else { throw Failure(text: "Missing demo offers") }
            var report: [String: Any] = ["normal_campaign_accessed":false,"physical_device_used":!Self.isSimulator,"timing":"reconstructed","ui_input_scope":"Shared production views/controllers; controller taps are automatic. Touch-event tests are separate."]
            for (name,offer,count,balance) in [("single",single,1,9500),("multi",multi,11,4500)] {
                status = "Committing isolated " + name
                let freshOffer = try await backend.quote(bannerID:banner.id,offer:offer.offer).transactionOffer
                let ok = await model.summon(banner,offer: freshOffer,using: backend,identity: "character-diagnostic")
                try require(ok,"Isolated summon failed")
                guard let committed = model.committedSummon else { throw Failure(text: "Missing receipt") }
                try require(committed.awards.count == count,"Incorrect award count")
                let before = try digest(save), calls = backend.requests
                let control = CharacterRevealController(receipt: committed)
                character = control;receipt = committed;callbacks = 0;returned = [];showGrid = false;coverDismissed = false;presenting = true
                try await wait { crystal.tapPhase == .fallingCrystals && (crystal.entranceElapsed ?? 0)>0.4 }
                try snapshot(root.appendingPathComponent(name+"-falling-begin.png"))
                try await wait { crystal.tapPhase == .fallingCrystals && (crystal.entranceElapsed ?? 0)>1.4 }
                try require(crystal.visibleFallingCount >= 2,"Multiple falling crystals unavailable")
                try snapshot(root.appendingPathComponent(name+"-falling-mid.png"))
                try await wait { crystal.tapPhase == .arriving }
                try snapshot(root.appendingPathComponent(name+"-main-arrival.png"))
                try await wait { crystal.tapPhase == .waitingForTap }
                try snapshot(root.appendingPathComponent(name+"-crystal-wait.png"))
                try require(crystal.tapToBreak(),"Crystal did not accept tap")
                try await wait { control.hasStarted }
                for index in 0..<count {
                    try require(control.state.index == index,"Reveal index skipped")
                    if index == 0 {
                        try await wait { control.state.phase == .flash || control.state.reason != nil }
                        try require(control.state.reason == nil,"Missing original assets or awarded sprite")
                        try snapshot(root.appendingPathComponent(name+"-flash.png"))
                        try await wait { control.state.phase == .materializing && control.state.progress > 0.35 }
                        try snapshot(root.appendingPathComponent(name+"-materializing.png"))
                        control.suspend();let held = control.state.elapsed
                        try await Task.sleep(nanoseconds: 150_000_000)
                        try require(control.state.elapsed == held && !control.isTicking,"Background simulation advanced")
                        control.resume()
                        try await wait { control.state.phase == .obtained && control.state.progress > 0.5 }
                        try snapshot(root.appendingPathComponent(name+"-obtained.png"))
                    }
                    try await wait { control.state.phase == .waitingForContinue || control.state.reason != nil }
                    try require(control.state.reason == nil && control.state.current?.instance_id == committed.awards[index].instance_id,"Award identity changed")
                    try require(control.display?.masterID == committed.awards[index].unit_id && control.sprite != nil,"Exact sprite missing")
                    if index == 0 {
                        try snapshot(root.appendingPathComponent(name+"-waiting.png"))
                        control.suspend();control.tap(expectedInstanceID: committed.awards[index].instance_id)
                        try await Task.sleep(nanoseconds: 100_000_000)
                        try require(control.state.index == index && control.state.phase == .waitingForContinue,"Inactive tap advanced")
                        control.resume()
                    }
                    let id = committed.awards[index].instance_id
                    control.tap(expectedInstanceID: id)
                    for _ in 0..<30 { control.tap(expectedInstanceID: id) }
                    try require(control.state.index == min(index+1,count-1),"Rapid taps skipped an award")
                }
                try await wait { callbacks == 1 && !presenting && coverDismissed }
                try require(control.callbackCount == 1 && !control.isTicking && control.images.isEmpty && control.sprite == nil,"Resources/callback not cleaned")
                try require(CommittedSummon.sameAwards(returned,committed.awards),"Result grid changed awards")
                try require(backend.requests == calls && model.campaign?.currencies["lapis_free"] == balance && (try digest(save)) == before,"Reveal performed a transaction or changed save")
                try await Task.sleep(nanoseconds: 400_000_000)
                try snapshot(root.appendingPathComponent(name+"-results.png"))
                report[name] = ["award_ids":committed.awards.map(\.instance_id),"master_ids":committed.awards.map(\.unit_id),"rarities":committed.awards.map { $0.granted_rarity ?? -1 },"count":count,"callbacks":callbacks,"save_unchanged_during_reveals":true,"resource_cleanup":true,"lapis":balance]
            }
            guard let committed = model.committedSummon else { throw Failure(text: "Missing final receipt") }
            // Production controller fallback/cleanup/Skip are tested without another transaction.
            for reason in [CharacterRevealFinish.skipped,.failed,.interrupted] {
                let control = CharacterRevealController(receipt: committed);var notifications = 0
                control.onCompletion = { _,awards in if CommittedSummon.sameAwards(awards,committed.awards) {notifications += 1} }
                control.begin(active: true);control.finish(reason);control.finish(reason)
                try require(notifications == 1 && !control.isTicking && control.images.isEmpty,"Skip/failure cleanup failed")
            }
            let corruptFolder = root.appendingPathComponent("corrupt-art")
            try FileManager.default.copyItem(at: Bundle.main.resourceURL!.appendingPathComponent("CharacterReveal"),to: corruptFolder)
            try Data("bad PNG".utf8).write(to: corruptFolder.appendingPathComponent("get.png"))
            let corrupt = CharacterRevealController(receipt: committed);var corruptFallback = 0
            corrupt.onCompletion = { reason,_ in if reason == .unavailable { corruptFallback += 1 } }
            corrupt.begin(active: true,directory: corruptFolder)
            try require(corruptFallback == 1 && corrupt.images.isEmpty && !corrupt.isTicking,"Corrupt original-art derivative did not fall back")
            for _ in 0..<40 {
                let stress = CharacterRevealController(receipt: committed)
                stress.begin(active: true);stress.finish(.skipped)
                try require(stress.images.isEmpty && stress.sprite == nil && !stress.isTicking,"Repeated reveal leaked resources")
            }
            let absent = CharacterRevealController(receipt: committed);var fallback = 0
            absent.onCompletion = { reason,awards in if reason == .unavailable && CommittedSummon.sameAwards(awards,committed.awards) { fallback += 1 } }
            absent.begin(active: true,directory: root.appendingPathComponent("missing-art"))
            try require(fallback == 1,"Missing-art fallback failed")
            let missingUnit = CommittedSummon(id: UUID(),bannerID: "visual-fixture",offerID: "none",backendIdentity: "no-transaction",awards: [Award(instance_id: "fixture",unit_id: "000000000",name: nil,granted_rarity: 3)])
            let missingSprite = CharacterRevealController(receipt: missingUnit);var missing = 0
            missingSprite.onCompletion = { reason,_ in if reason == .unavailable { missing += 1 } }
            missingSprite.begin(active: true);try require(missing == 1,"Missing unit sprite did not fall back")
            // Weak-target display links must not retain otherwise released controllers.
            weak var released: CharacterRevealController?
            autoreleasepool {
                let temp = CharacterRevealController(receipt: committed);released = temp;temp.begin(active: true)
            }
            try require(released == nil,"Display link retained a released controller")
            try write(["relative_root":relative,"award_ids":committed.awards.map(\.instance_id),"lapis":4500,"save_sha256":try digest(save)],base.appendingPathComponent("last-test.json"))
            report["status"] = "passed";report["backend_requests"] = backend.requests;report["successful_commits"] = backend.commits
            report["skip_failure_missing_art_cleanup"] = true;report["weak_controller_release"] = true;report["repeated_resource_cycles"] = 40;report["corrupt_art_fallback"] = true
            report["relative_root"] = relative;report["callback_count_per_sequence"] = 1
            try write(report,base.appendingPathComponent("report.json"));status = "Passed · isolated single and eleven sequential reveals"
        } catch {
            status = String(describing: error)
            if let folder { try? write(["status":"failed","error":status,"normal_campaign_accessed":false,"character_phase":character?.state.phase.rawValue ?? "none","character_started":character?.hasStarted ?? false,"character_reason":character?.state.reason?.rawValue ?? "none","crystal_phase":crystal.tapPhase?.rawValue ?? "none"],folder.appendingPathComponent("report.json")) }
        }
    }
    @MainActor private func wait(_ predicate: () -> Bool) async throws {
        for _ in 0..<350 { if predicate() { return };try await Task.sleep(nanoseconds: 20_000_000) }
        throw Failure(text: "Timed out waiting for production presentation")
    }
    private func write(_ value: [String: Any],_ url: URL) throws {
        try JSONSerialization.data(withJSONObject: value,options: [.prettyPrinted,.sortedKeys]).write(to: url,options: .atomic)
    }
    private func digest(_ url: URL) throws -> String { SHA256.hash(data: try Data(contentsOf: url)).map { String(format: "%02x",$0) }.joined() }
    @MainActor private func snapshot(_ url: URL) throws {
        guard let window = UIApplication.shared.connectedScenes.compactMap({ $0 as? UIWindowScene }).flatMap(\.windows).first(where: \.isKeyWindow) else { throw Failure(text: "No Simulator window") }
        let image = UIGraphicsImageRenderer(bounds: window.bounds).image { _ in window.drawHierarchy(in: window.bounds,afterScreenUpdates: true) }
        guard let png = image.pngData() else { throw Failure(text: "Screenshot encoding failed") }
        try png.write(to: url)
    }
}
