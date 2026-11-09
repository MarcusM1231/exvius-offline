import SwiftUI
import UIKit

struct SummonAnchor: Decodable {
    let x: Double, y: Double, width: Double, height: Double
    let texture: String
}
struct SummonImageEntry: Decodable { let file: String; let width: Double; let height: Double }
final class SummonUIResources {
    struct Catalog: Decodable {
        let schema: Int
        let layouts: [String: [String: SummonAnchor]]
        let assets: [String: SummonImageEntry]
    }
    static let shared = SummonUIResources(directory: Bundle.main.resourceURL?.appendingPathComponent(
        ProcessInfo.processInfo.arguments.contains("--ui-assets-missing") ? "SummonUI-Missing" : "SummonUI"))
    let catalog: Catalog?
    let directory: URL?
    private var images: [String: UIImage] = [:]
    init(directory: URL? = Bundle.main.resourceURL?.appendingPathComponent("SummonUI")) {
        self.directory = directory
        catalog = directory.flatMap { try? Data(contentsOf: $0.appendingPathComponent("catalog.json")) }
            .flatMap { try? JSONDecoder().decode(Catalog.self, from: $0) }
    }
    func image(_ id: String) -> UIImage? {
        if let image = images[id] { return image }
        guard catalog?.schema == 1, let row = catalog?.assets[id],
              row.file == "images/\(id).png", let directory,
              let image = UIImage(contentsOfFile: directory.appendingPathComponent(row.file).path) else { return nil }
        images[id] = image
        return image
    }
    func anchor(_ layout: String, _ name: String) -> SummonAnchor? { catalog?.layouts[layout]?[name] }
}

struct SummonArt: View {
    let id: String
    var body: some View {
        if let image = SummonUIResources.shared.image(id) {
            Image(uiImage: image).resizable()
        } else {
            ZStack { Color(red: 0.08, green: 0.12, blue: 0.22); Text("UI artwork unavailable").font(.caption).foregroundStyle(.white) }
                .accessibilityIdentifier("missing-ui-\(id)")
        }
    }
}
private let gold = Color(red: 0.96, green: 0.83, blue: 0.48)
private let ink = Color(red: 0.025, green: 0.045, blue: 0.10)

// Original 640×1136 layout is a region map, not a SwiftUI frame. The old global
// header occupies y=0...172; our safe-area currency/navigation replaces that band.
// Preserve x and relative y within the remaining region; uniformly scale by width.
struct GlobalAnchorPosition: ViewModifier {
    let anchor: SummonAnchor
    func body(content: Content) -> some View {
        content.frame(width: anchor.width, height: anchor.height)
            .position(x: anchor.x + anchor.width/2, y: anchor.y - 172 + anchor.height/2)
    }
}
private func anchor(_ layout: String, _ name: String, fallback: SummonAnchor) -> SummonAnchor {
    SummonUIResources.shared.anchor(layout, name) ?? fallback
}

struct SummonOfferButton: View {
    let offer: Offer
    let enabled: Bool
    let action: () -> Void
    // Never use baked-in "11 Summons" lettering for a different count/currency.
    private var art: String? {
        guard offer.cost?.kind == "lapis", [1,11].contains(offer.draws) else { return nil }
        let id = offer.draws == 1 ? "single" : "eleven"
        return SummonUIResources.shared.image(id) == nil ? nil : id
    }
    var body: some View {
        Button(action: action) {
            ZStack {
                if art == nil { OriginalMenuArt(id:"confirm-button"); Text("Summon ×\(offer.draws)").offset(y: -16) }
                Text(art != nil ? String(offer.cost?.amount ?? 0) : (offer.cost?.label ?? "Free"))
                    .font(.system(size: 21, weight: .bold))
                    .foregroundStyle(.white).shadow(color: .black, radius: 1).offset(x: art == nil ? 0 : 20, y: 24)
            }.frame(width: 304, height: 136).contentShape(Rectangle())
        }.buttonStyle(RecoveredSummonButtonStyle(art: art)).disabled(!enabled).opacity(enabled ? 1 : 0.5)
            .accessibilityLabel("Summon \(offer.draws), \(offer.cost?.label ?? "Free")")
            .accessibilityIdentifier("summon-offer-\(offer.offer)")
    }
}

private struct RecoveredSummonButtonStyle: ButtonStyle {
    let art: String?
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.background {
            if let art { SummonArt(id: art + (configuration.isPressed ? "-down" : "")) }
        }
    }
}

struct BannerArtwork: View {
    let banner: Banner
    var compact = false
    var body: some View {
        ZStack {
            SummonArt(id: "background-top")
            LinearGradient(colors: [.black.opacity(0.05), .black.opacity(0.7)], startPoint: .top, endPoint: .bottom)
            VStack(spacing: compact ? 6 : 12) {
                Text("FFBE REVIVAL").font(.system(size: compact ? 16 : 20, weight: .semibold, design: .serif)).tracking(5)
                Text(banner.name).font(.system(size: compact ? 25 : 32, weight: .bold, design: .serif)).multilineTextAlignment(.center).lineLimit(compact ? 2 : 4).minimumScaleFactor(0.8)
                Text("DEMO BANNER · \(banner.id)").font(.system(size: compact ? 15 : 17)).tracking(2)
            }.foregroundStyle(.white).shadow(color: .black, radius: 3).padding(compact ? 12 : 25)
        }.clipped().overlay(Rectangle().stroke(gold.opacity(0.8), lineWidth: 2))
    }
}

struct GlobalSummonScreen: View {
    @ObservedObject var model: SummonModel
    let summon: (Banner, Offer) async -> Bool
    let refresh: () async -> Void
    let quote: ((Banner, Offer) async -> MenuQuote?)?
    @State private var pendingQuote: MenuQuote?
    @State private var selected: Banner?
    @State private var pending: Offer?
    @State private var showResults = false
    @State private var reliableResults = false
    @State private var requestInFlight = false
    @State private var confirmationDismissed = true
    @State private var pendingReveal: CommittedSummon?
    @State private var crystalCover: CommittedSummon?
    @State private var presentedAwards: [Award]?
    init(model: SummonModel, initialBanner: Banner? = nil, results: Bool = false,
         refresh: @escaping () async -> Void = {}, quote: ((Banner, Offer) async -> MenuQuote?)? = nil, summon: @escaping (Banner, Offer) async -> Bool) {
        self.model = model; self.summon = summon; self.refresh = refresh; self.quote = quote
        _selected = State(initialValue: initialBanner)
        _showResults = State(initialValue: results)
        _presentedAwards = State(initialValue: results ? model.results : nil)
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                if showResults {
                    Button { selected = nil; showResults = false } label: { Label("Banners", systemImage: "chevron.left") }
                        .disabled(model.busy)
                } else { Text("SUMMON").font(.system(.title2, design: .serif).bold()).foregroundStyle(gold) }
                Spacer()
                SummonArt(id: "lapis").scaledToFit().frame(width: 22, height: 26)
                Text("\(lapis)").monospacedDigit().bold().accessibilityIdentifier("lapis-balance")
            }.padding(.horizontal, 16).padding(.vertical, 12).background {
                OriginalMenuArt(id:"header-background").overlay(alignment:.bottom) {OriginalMenuArt(id:"header-decoration").scaledToFit()}
            }
            if model.busy { ProgressView("Saving summon…").tint(gold).padding(8) }
            if let error = model.error {
                VStack(spacing: 8) {
                    Text(error).font(.callout).accessibilityIdentifier("summon-error")
                    Button("Refresh saved state") { Task { await refresh() } }
                        .buttonStyle(.bordered).disabled(model.busy)
                }.foregroundStyle(.white).padding(12).frame(maxWidth: .infinity).background(Color.red.opacity(0.45))
            }
            if SummonUIResources.shared.catalog == nil {
                Text("Original UI assets unavailable · using accessible fallback controls.").font(.caption).padding(8)
            }
            if showResults {
                GlobalSummonResults(awards: presentedAwards ?? model.results, reliable: $reliableResults) {
                    showResults = false; selected = nil
                }
            } else {
                OriginalBannerMenu(model: model, initialID: selected?.id, choose: { banner, offer in
                    guard !requestInFlight, !model.busy, !model.needsRefresh else { return }
                    let live = if let quote { await quote(banner,offer) } else { model.menuCatalog?.banners.first(where: {$0.id==banner.id})?.offers.first(where: {$0.offer==offer.offer}) }
                    guard let live else { model.error = "Could not refresh this summon offer."; return }
                    pendingQuote = live
                    selected = banner
                    confirmationDismissed = false
                    pending = live.transactionOffer
                }, latest: {
                    presentedAwards = model.results; showResults = true
                })
            }
        }.background(ink).foregroundStyle(.white)
            .fullScreenCover(item: $pending, onDismiss: { confirmationDismissed = true; presentCommittedIfReady() }) { offer in
                if let banner = selected {
                    SummonConfirmation(banner: banner, offer: offer, balance: pendingQuote?.balance ?? lapis, busy: model.busy, quote: pendingQuote) {
                        guard !requestInFlight else { return }
                        requestInFlight = true
                        let priorReceipt = model.committedSummon?.id
                        pending = nil
                        Task {
                            defer { requestInFlight = false }
                            if await summon(banner, offer) {
                                guard let receipt = model.committedSummon,
                                      receipt.id != priorReceipt, receipt.bannerID == banner.id,
                                      receipt.offerID == offer.offer,
                                      CommittedSummon.sameAwards(receipt.awards, model.results) else {
                                    // Never invent a crystal for an uncorrelated callback.
                                    // Saved-state recovery remains available; no automatic retry.
                                    presentedAwards = model.campaign?.last_pull?.awards ?? model.results
                                    showResults = true
                                    return
                                }
                                pendingReveal = receipt
                                presentCommittedIfReady()
                            }
                        }
                    }
                }
            }
            .fullScreenCover(item: $crystalCover, onDismiss: {
                if let receipt = pendingReveal { reveal(receipt.id, awards: receipt.awards) }
            }) { receipt in
                CommittedSummonPresentation(receipt: receipt) { awards in
                    reveal(receipt.id, awards: awards)
                }.id(receipt.id)
            }
    }
    private func presentCommittedIfReady() {
        guard confirmationDismissed, let receipt = pendingReveal, crystalCover == nil else { return }
        crystalCover = receipt
    }
    private func reveal(_ id: UUID, awards: [Award]) {
        guard let receipt = pendingReveal, receipt.id == id else { return }
        // Use the immutable receipt even if lifecycle refresh changed model.results.
        presentedAwards = receipt.awards
        pendingReveal = nil; crystalCover = nil; showResults = true
    }
    private var lapis: Int { (model.campaign?.currencies["lapis_free"] ?? 0)+(model.campaign?.currencies["lapis_paid"] ?? 0) }
    private var banners: some View {
        ZStack(alignment: .topLeading) {
            Text("Summon a new ally").font(.system(size: 30, weight: .bold, design: .serif)).foregroundStyle(gold)
                .frame(width: 640).position(x: 320, y: 55)
            SummonArt(id: "tabs").modifier(GlobalAnchorPosition(anchor: anchor("top", "gacha_tab_offset", fallback: .init(x:0,y:250,width:640,height:86,texture:""))))
            Text("Select a banner").font(.system(size: 21)).frame(width: 640).position(x: 320, y: 121)
            ForEach(Array(model.banners.enumerated()), id: \.element.id) { index, banner in
                Button { selected = banner } label: { BannerArtwork(banner: banner, compact: true) }
                    .buttonStyle(.plain).frame(width: 640, height: 160)
                    .position(x: 320, y: (SummonUIResources.shared.anchor("top", "common_banner")?.y ?? 338)-172+80+Double(index)*190)
                    .accessibilityIdentifier("banner-\(banner.id)")
            }
            Button("View latest saved summon") {
                if let receipt = pendingReveal { reveal(receipt.id,awards: receipt.awards) }
                else { presentedAwards = model.results; showResults = true }
            }
                .font(.system(size: 23, weight: .semibold)).foregroundStyle(gold)
                .disabled(model.busy || requestInFlight || model.campaign == nil)
                .frame(width: 600, height: 70).position(x: 320, y: Double(model.banners.count)*190+210)
        }
    }
    private func detail(_ banner: Banner) -> some View {
        ZStack(alignment: .topLeading) {
            BannerArtwork(banner: banner).modifier(GlobalAnchorPosition(anchor: anchor("detail", "gacha_banner", fallback: .init(x: 0,y: 250,width: 640,height: 392,texture: ""))))
            ForEach(Array(banner.offer_details.enumerated()), id: \.element.id) { index, offer in
                let name = banner.offer_details.count == 1 ? "gacha_btn_center_offset" : index == 0 ? "gacha_btn_left_offset" : "gacha_btn_right_offset"
                SummonOfferButton(offer: offer, enabled: banner.supported && !requestInFlight && !model.busy && !model.needsRefresh && pendingReveal == nil) { confirmationDismissed = false; pending = offer }
                    .modifier(GlobalAnchorPosition(anchor: anchor("detail", name, fallback: .init(x: Double(index)*320,y: 653,width: 304,height: 136,texture: ""))))
            }
            Text("Confirm the cost before summoning.\nYour summoned allies are saved on this device.")
                .font(.system(size: 22)).multilineTextAlignment(.center).foregroundStyle(.white.opacity(0.8))
                .frame(width: 580,height: 110).position(x: 320,y: 690)
            if !banner.supported { Text("This banner is not supported.").position(x:320,y:600) }
        }
    }
}

struct SummonConfirmation: View {
    let banner: Banner
    let offer: Offer
    let balance: Int
    let busy: Bool
    var quote: MenuQuote? = nil
    let confirm: () -> Void
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        ZStack {
            Color.black.opacity(0.92).ignoresSafeArea()
            ScrollView {
                VStack(spacing:22) {
                    Text("CONFIRM SUMMON").font(.system(.title2,design:.serif).bold()).foregroundStyle(gold)
                    Text(banner.name).font(.headline).multilineTextAlignment(.center)
                    Text("Summon ×\(offer.draws)").font(.title2)
                    Text("Cost: \(offer.cost?.label ?? "Free")").font(.title3.bold())
                    Text("\(offer.cost?.kind == "lapis" ? "Lapis balance":"Available balance"): \(balance)").monospacedDigit()
                    if let quote {Text(quote.guarantee).font(.callout);if !quote.reason.isEmpty {Text(quote.reason).foregroundStyle(gold)}}
                    OriginalMenuButton(title:"Confirm · \(offer.cost?.label ?? "Free")",enabled:!busy && (quote?.eligible ?? ((offer.cost?.amount ?? 0)<=balance)),action:confirm)
                        .accessibilityIdentifier("confirm-summon")
                    OriginalMenuButton(title:"Cancel") {dismiss()}
                }.padding(28).frame(maxWidth:480)
                    .background {OriginalMenuArt(id:"window")}
            }.frame(maxWidth:520,maxHeight:560).padding(20)
        }.foregroundStyle(.white)
    }
}

struct GlobalSummonResults: View {
    let awards: [Award]
    @Binding var reliable: Bool
    let back: () -> Void
    var body: some View {
        GeometryReader { geometry in
        let scale = min(geometry.size.width, 760) / 640
        let resultTop = max(64, ((SummonUIResources.shared.anchor("result", "gacha_result_area2")?.y ?? 312)-172)*scale)
        ScrollView {
            VStack(spacing: 18) {
                Text("SUMMON RESULTS").font(.system(.title2,design: .serif).bold()).foregroundStyle(gold).frame(height: resultTop-18)
                if awards.isEmpty { Text("No saved summon yet.") }
                // The original result-area anchors are recovered. Tile generation is
                // not: this adaptive grid is explicitly documented as a reconstruction.
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 105,maximum: 160), spacing: 10)],spacing: 16) {
                    ForEach(awards) { award in
                        let unit = UnitCatalog.display(masterID: award.unit_id, backendName: award.name, rarity: award.granted_rarity, isAward: true)
                        VStack(spacing: 5) {
                            UnitArtworkView(unit: unit)
                            Text(unit.name).font(.system(size: 13,weight: .semibold)).multilineTextAlignment(.center).lineLimit(3)
                            Text(unit.rarity).font(.caption).foregroundStyle(gold)
                            Text(award.unit_id).font(.system(size: 9)).foregroundStyle(.white.opacity(0.6))
                        }.frame(maxWidth: .infinity,minHeight: 155).padding(.vertical,8)
                            .background { SummonArt(id: "plate").opacity(0.6) }
                    }
                }
                Button("Return to banners", action: back).buttonStyle(.borderedProminent).tint(.brown)
                Button("View plain result list") { reliable = true }.font(.caption).foregroundStyle(gold)
            }.padding(.horizontal,16).padding(.bottom,25)
                .frame(maxWidth: 760).frame(maxWidth: .infinity)
        }.background { SummonArt(id: "cosmos").scaledToFill().clipped().opacity(0.5) }
        }.clipped().sheet(isPresented: $reliable) {
                NavigationStack {
                    List(awards) { award in
                        UnitRowView(unit: UnitCatalog.display(masterID: award.unit_id, backendName: award.name, rarity: award.granted_rarity, isAward: true),inventoryDetail: nil)
                    }.navigationTitle("Saved summon").toolbar { Button("Done") { reliable = false } }
                }
            }
    }
}
