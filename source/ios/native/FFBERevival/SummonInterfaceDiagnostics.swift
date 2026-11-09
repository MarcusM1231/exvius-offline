import SwiftUI

// Explicit test launch only. All transactions use a fresh isolated diagnostic
// campaign. No normal campaign or fabricated award is used for UI screenshots.
struct SummonInterfaceDiagnostics: View {
    @StateObject private var model = SummonModel()
    @State private var status = "Checking isolated campaign…"
    @State private var ready = false
    @State private var reliable = false
    @State private var backend: EmbeddedSummonBackend?
    private var page: String {
        let a = ProcessInfo.processInfo.arguments
        guard let i = a.firstIndex(of: "--ui-page"), a.count > i+1 else { return "banners" }
        return a[i+1]
    }
    var body: some View {
        VStack(spacing: 0) {
            Text("ISOLATED UI TEST · \(status)").font(.caption2).padding(5).frame(maxWidth: .infinity).background(.yellow).foregroundStyle(.black)
            if ready {
                if page == "confirmation", let banner = model.banners.first, let offer = banner.offer_details.last {
                    SummonConfirmation(banner: banner, offer: offer, balance: 4500, busy: true, confirm: {})
                } else {
                    GlobalSummonScreen(model: model, initialBanner: page == "details" ? model.banners.first : nil, results: page == "results") { banner, offer in
                        guard let backend else { return false }
                        return await model.summon(banner, offer: offer, using: backend, identity: "diagnostic")
                    }
                }
            } else { ProgressView(status).frame(maxWidth: .infinity,maxHeight: .infinity) }
        }.task { await check() }
    }
    @MainActor private func check() async {
        do {
            let root = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation/ui-" + UUID().uuidString)
            let engine = EmbeddedSummonBackend(storage: root.appendingPathComponent("campaign"))
            backend = engine
            await model.refresh(using: engine,identity: "diagnostic")
            guard let banner = model.banners.first(where: { $0.id == "9100203" }), let single = banner.offer_details.first,
                  let multi = banner.offer_details.last else { throw APIError(message: "Missing offers") }
            async let first = model.summon(banner,offer: single,using: engine,identity: "diagnostic")
            async let duplicate = model.summon(banner,offer: single,using: engine,identity: "diagnostic")
            let pair = await (first, duplicate)
            let one = [pair.0, pair.1].filter { $0 }.count == 1
            guard one, model.results.count == 1, model.campaign?.currencies["lapis_free"] == 9500 else { throw APIError(message: "Single transaction failed") }
            let refreshedMulti = try await engine.quote(bannerID:banner.id,offer:"secondary").transactionOffer
            let many = await model.summon(banner,offer: refreshedMulti,using: engine,identity: "diagnostic")
            guard many, model.results.count == 11, model.campaign?.currencies["lapis_free"] == 4500 else { throw APIError(message: "Multi transaction failed") }
            let saved = model.results.map(\.instance_id)
            let insufficientOffer = try await engine.quote(bannerID:banner.id,offer:"secondary").transactionOffer
            let rejected = await model.summon(banner,offer: insufficientOffer,using: engine,identity: "diagnostic")
            guard !rejected, model.results.map(\.instance_id) == saved, model.needsRefresh else { throw APIError(message: "Failure displayed new rewards") }
            await model.refresh(using: engine,identity: "diagnostic")
            guard model.results.map(\.instance_id) == saved else { throw APIError(message: "Saved results changed") }
            let resources = SummonUIResources.shared
            let missingMode = ProcessInfo.processInfo.arguments.contains("--ui-assets-missing")
            let assetCount: Int
            if missingMode {
                guard resources.catalog == nil else { throw APIError(message: "Missing-assets test loaded content") }
                assetCount = 0
            } else {
                guard let catalog = resources.catalog, catalog.assets.keys.allSatisfy({ resources.image($0) != nil }) else { throw APIError(message: "UI dependency failed to decode") }
                assetCount = catalog.assets.count
            }
            let missing = SummonUIResources(directory: root.appendingPathComponent("absent"))
            guard missing.image("single") == nil else { throw APIError(message: "Missing UI did not fall back") }
            var rendered = 0
            for width in [320.0,393.0,440.0,768.0] {
                let view = GlobalSummonScreen(model: model,initialBanner: banner,results: false,summon: { _,_ in false }).frame(width: width,height: 760)
                let renderer = ImageRenderer(content: view)
                guard renderer.uiImage != nil else { throw APIError(message: "Size rendering failed") }
                rendered += 1
            }
            let report: [String: Any] = ["status":"passed","single":true,"duplicate_submission_blocked":true,"multi":true,"insufficient_currency":true,
                "failure_kept_saved_results":true,"normal_campaign_accessed":false,"assets_decoded":assetCount,"missing_asset_mode":missingMode,
                "widths_rendered":rendered,"missing_assets_fallback":true,"network":"embedded backend network guard remains enabled",
                "ui_page":page,"diagnostic_campaign":root.path]
            let folder=root.deletingLastPathComponent()
            try FileManager.default.createDirectory(at: folder,withIntermediateDirectories: true)
            try JSONSerialization.data(withJSONObject: report,options: [.prettyPrinted,.sortedKeys])
                .write(to: folder.appendingPathComponent("summon-ui-report.json"),options: .atomic)
            status = "passed · single / multi / refusal"
            ready = true
        } catch { status = error.localizedDescription }
    }
}
