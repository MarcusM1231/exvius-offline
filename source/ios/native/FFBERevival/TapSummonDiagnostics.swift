import SwiftUI

@MainActor final class CountedEmbeddedBackend: SummonBackend {
    let base: EmbeddedSummonBackend
    let journal: URL
    private(set) var requests = 0
    private(set) var commits = 0
    init(storage: URL,journal: URL) { base = EmbeddedSummonBackend(storage: storage); self.journal = journal }
    func menu() async throws -> MenuCatalog { try await base.menu() }
    func quote(bannerID: String,offer: String) async throws -> MenuQuote { try await base.quote(bannerID:bannerID,offer:offer) }
    func banners() async throws -> BannersResponse { try await base.banners() }
    func state() async throws -> Campaign { try await base.state() }
    func summon(bannerID: String,offer: String) async throws -> SummonResponse {
        requests += 1
        defer { try? JSONSerialization.data(withJSONObject: ["requests":requests,"successful_responses":commits],options: [.sortedKeys]).write(to: journal,options: .atomic) }
        let result = try await base.summon(bannerID: bannerID,offer: offer)
        commits += 1; return result
    }
}

// Explicit launch-only harness. No default campaign or normal backend instance.
struct TapSummonDiagnostics: View {
    @StateObject private var model = SummonModel()
    @StateObject private var renderer = CrystalReconstructionController()
    @State private var backend: CountedEmbeddedBackend?
    @State private var ready = false
    @State private var status = "Preparing isolated campaign…"
    private var lab: Bool { ProcessInfo.processInfo.arguments.contains("--tap-summon-lab") || ProcessInfo.processInfo.arguments.contains("--character-reveal-lab") }
    private var reload: Bool { ProcessInfo.processInfo.arguments.contains("--tap-summon-reload-check") }
    var body: some View {
        VStack(spacing: 0) {
            Text("ISOLATED TAP SUMMON TEST · " + status).font(.caption2).padding(6).frame(maxWidth: .infinity).background(.purple).foregroundStyle(.white)
            if ready {
                GlobalSummonScreen(model: model,initialBanner: lab ? model.banners.first { $0.id == "9100203" } : nil,results: !lab) { banner,offer in
                    guard let backend else { return false }
                    return await model.summon(banner,offer: offer,using: backend,identity: "tap-diagnostic")
                }
            } else {
                ReconstructedCrystalViewport(controller: renderer).frame(height: 400)
                Text(status).font(.caption).padding()
            }
        }.background(.black).preferredColorScheme(.dark).task { await check() }
    }
    private struct CheckFailure: Error { let text: String }
    @MainActor private func check() async {
        var folder: URL?
        do {
            func require(_ value: Bool,_ text: String) throws { if !value { throw CheckFailure(text: text) } }
            let base = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation/tap-summon")
            try FileManager.default.createDirectory(at: base,withIntermediateDirectories: true); folder = base
            var expected: [String: Any] = [:]
            let relative: String
            if reload {
                expected = try JSONSerialization.jsonObject(with: Data(contentsOf: base.appendingPathComponent("last-test.json"))) as? [String: Any] ?? [:]
                guard let root = expected["relative_root"] as? String, root.hasPrefix("run-"),UUID(uuidString: String(root.dropFirst(4))) != nil else { throw CheckFailure(text: "Missing isolated recovery marker") }
                relative = root
            } else { relative = "run-"+UUID().uuidString }
            let engine = CountedEmbeddedBackend(storage: base.appendingPathComponent(relative+"/campaign"),journal: base.appendingPathComponent(lab ? "lab-counters.json" : "counters.json"))
            backend = engine; await model.refresh(using: engine,identity: "tap-diagnostic")
            try require(model.campaign != nil && !model.needsRefresh,"Isolated backend initialization failed")
            if lab { status = "Fresh test campaign · no real progress used"; ready = true; return }
            if reload {
                let ids = expected["award_ids"] as? [String] ?? []
                try require(!ids.isEmpty && model.results.map(\.instance_id) == ids,"Cold recovery changed saved awards")
                try require(model.campaign?.currencies["lapis_free"] == expected["lapis"] as? Int && engine.requests == 0,"Cold reload charged or called summon")
                try write(["status":"passed","cold_relaunch":true,"summon_requests":engine.requests,"award_ids":ids,"lapis":model.campaign?.currencies["lapis_free"] ?? -1,"normal_campaign_accessed":false],to: base.appendingPathComponent("reload-report.json"))
                status = "Cold reload passed · zero summon requests"; ready = true; return
            }
            guard let banner = model.banners.first(where: { $0.id == "9100203" }),let single = banner.offer_details.first,let multi = banner.offer_details.last else { throw CheckFailure(text: "Missing diagnostic offers") }
            status = "Checking one committed single…"
            async let one = model.summon(banner,offer: single,using: engine,identity: "tap-diagnostic")
            async let duplicate = model.summon(banner,offer: single,using: engine,identity: "tap-diagnostic")
            let pair = await [one,duplicate]
            try require(pair.filter { $0 }.count == 1 && engine.requests == 1 && engine.commits == 1,"Duplicate confirmation created another request")
            guard let receipt = model.committedSummon else { throw CheckFailure(text: "Missing correlated receipt") }
            try require(receipt.awards.count == 1 && model.campaign?.currencies["lapis_free"] == 9500,"Single award/cost changed")
            renderer.load(); try require(renderer.ready,"Renderer unavailable")
            var completions = 0
            renderer.onCompletion = { _ in completions += 1 }
            renderer.appearance = receipt.crystalAppearance; renderer.startTapPresentation()
            try require(!renderer.tapToBreak(),"Arrival tap was not ignored")
            try await Task.sleep(nanoseconds: UInt64((CrystalEntranceTiming.totalArrival+0.4)*1_000_000_000))
            try require(renderer.tapPhase == .waitingForTap,"Arrival did not enter waiting")
            status = "Waiting beyond old auto-open deadline…"
            try await Task.sleep(nanoseconds: 3_400_000_000)
            try require(renderer.tapPhase == .waitingForTap && completions == 0,"Crystal opened without a tap")
            let motionBefore = renderer.productionMotionTime ?? -1
            try await Task.sleep(nanoseconds: 1_500_000_000)
            try require((renderer.productionMotionTime ?? -1)>motionBefore && renderer.productionSourceTime == 0.9 && renderer.tapPhase == .waitingForTap,"Idle motion reset or opening progression advanced")
            try renderer.snapshot().pngData()?.write(to: base.appendingPathComponent("waiting-for-tap.png"))
            renderer.suspend(); try require(!renderer.tapToBreak(),"Inactive tap opened crystal")
            try await Task.sleep(nanoseconds: 100_000_000); renderer.resumeTapPresentation()
            try require(renderer.tapPhase == .waitingForTap,"Resume opened crystal")
            try require(renderer.tapToBreak(),"Valid tap failed")
            for _ in 0..<20 { try require(!renderer.tapToBreak(),"Repeated tap restarted opening") }
            try await Task.sleep(nanoseconds: 300_000_000)
            renderer.suspend(); try require(renderer.tapPhase == .opening && completions == 0,"Opening pause completed early")
            try renderer.snapshot().pngData()?.write(to: base.appendingPathComponent("opening.png"))
            renderer.resumeTapPresentation()
            for _ in 0..<40 {
                if completions != 0 { break }
                try await Task.sleep(nanoseconds: 100_000_000)
            }
            try require(completions == 1 && renderer.tapPhase == .finished && !renderer.isTicking,"Opening did not complete once")
            renderer.onCompletion = nil; renderer.stop()
            var gate = SummonRevealGate(receipt: receipt)
            try require(gate.finish()?.map(\.instance_id) == receipt.awards.map(\.instance_id) && gate.finish() == nil,"Skip/fallback changed awards or completed twice")
            status = "Checking committed 11-pull and recovery…"
            let many = await model.summon(banner,offer: multi,using: engine,identity: "tap-diagnostic")
            try require(many && model.results.count == 11 && engine.requests == 2 && engine.commits == 2,"Multi created duplicate requests")
            guard let multiReceipt = model.committedSummon else { throw CheckFailure(text: "Missing multi receipt") }
            try require(model.campaign?.currencies["lapis_free"] == 4500,"Multi cost changed")
            let missing = CrystalReconstructionController(); missing.load(directory: base.appendingPathComponent("absent"))
            var fallback = SummonRevealGate(receipt: multiReceipt); var fallbackCount = 0
            missing.onCompletion = { _ in if fallback.finish() != nil { fallbackCount += 1 } }
            missing.startTapPresentation(); missing.startTapPresentation()
            try require(!missing.ready && fallbackCount == 1,"Unavailable renderer fallback repeated")
            let saved = model.results.map(\.instance_id)
            let refused = await model.summon(banner,offer: multi,using: engine,identity: "tap-diagnostic")
            try require(!refused && model.committedSummon == nil && engine.commits == 2 && model.results.map(\.instance_id) == saved,"Refusal produced rewards")
            await model.refresh(using: engine,identity: "tap-diagnostic")
            try require(model.results.map(\.instance_id) == saved,"Saved recovery changed awards")
            try write(["relative_root":relative,"award_ids":saved,"lapis":4500],to: base.appendingPathComponent("last-test.json"))
            for appearance in CrystalAppearance.allCases {
                renderer.appearance = appearance; renderer.inspect()
                try renderer.snapshot().pngData()?.write(to: base.appendingPathComponent("appearance-"+appearance.rawValue.lowercased()+".png"))
            }
            renderer.stop()
            try write(["status":"passed","single_commits":1,"multi_commits":1,"backend_requests":engine.requests,"successful_commits":engine.commits,
                       "duplicate_confirmation_blocked":true,"waited_without_tap_seconds":4.9,"continuous_idle_motion":true,"no_auto_open":true,"arrival_tap_ignored":true,
                       "one_opening":true,"one_completion":true,"background_waiting_preserved":true,"background_opening_preserved":true,
                       "skip_preserves_awards":true,"missing_renderer_fallback":true,"insufficient_lapis_no_crystal":true,
                       "award_ids":saved,"lapis":4500,"normal_campaign_accessed":false,
                       "scope":"Real embedded backend + shared renderer + pure completion gate. Actual production UI touch/Skip is a separate manual check."],to: base.appendingPathComponent("report.json"))
            status = "Passed · one single + one multi · isolated"; ready = true
        } catch {
            renderer.onCompletion = nil; renderer.stop()
            status = "Failed: "+((error as? CheckFailure)?.text ?? error.localizedDescription)
            if let folder { try? write(["status":"failed","error":status],to: folder.appendingPathComponent("report.json")) }
        }
    }
    private func write(_ value: [String: Any],to url: URL) throws {
        try JSONSerialization.data(withJSONObject: value,options: [.sortedKeys,.prettyPrinted]).write(to: url,options: .atomic)
    }
}
