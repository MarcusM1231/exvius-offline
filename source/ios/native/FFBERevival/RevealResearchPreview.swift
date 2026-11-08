import SwiftUI
import UIKit

// Static, presentation-only research. No backend, campaign, timer or SceneKit nodes.
struct RevealResearchPreview: View {
    @State private var candidate = "getglow"
    @State private var showGlow = true
    @State private var showUnit = true
    @State private var showBackground = true
    private let candidates = ["getglow", "starglow", "stLight_3", "stLight_4", "stLight_5"]
    private let root = Bundle.main.resourceURL?.appendingPathComponent("RevealResearch")
    private var maria: UnitDisplay {
        UnitCatalog.display(masterID: "202000203", backendName: nil, rarity: 3, isAward: true)
    }
    private func artwork(_ id: String) -> UIImage? {
        guard let url = root?.appendingPathComponent(id + ".png") else { return nil }
        return UIImage(contentsOfFile: url.path)
    }
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Text("RECOVERED REVEAL CANDIDATES").font(.headline)
                Text("Research only · no summon or save access").font(.caption)
                Text("Original preservation artwork; reconstructed static placement. The remembered pedestal is not yet confirmed.")
                    .font(.caption).foregroundStyle(.secondary)
                Picker("Candidate", selection: $candidate) {
                    ForEach(candidates, id: \.self) { Text($0).tag($0) }
                }.pickerStyle(.menu)
                ZStack {
                    Color(red: 0.025, green: 0.025, blue: 0.06)
                    if showBackground, let image = artwork("cosmos") {
                        Image(uiImage: image).resizable().scaledToFill().opacity(0.65)
                            .frame(width: 300, height: 340).clipped()
                    }
                    if showGlow, let image = artwork(candidate) {
                        // Original atlas pixels, arbitrary preview scale/position; not decoded keyframes.
                        Image(uiImage: image).resizable().scaledToFit()
                            .frame(width: 240, height: 100).offset(y: 64).blendMode(.plusLighter)
                    }
                    if showUnit {
                        UnitArtworkView(unit: maria).scaleEffect(2).offset(y: -4)
                    }
                }.frame(width: 300, height: 340).clipped().accessibilityIdentifier("reveal-research-composite")
                Text(maria.name + " · " + maria.rarity).font(.headline)
                Text("Exact master ID 202000203 · static sprite").font(.caption)
                Toggle("Candidate layer", isOn: $showGlow)
                Toggle("Maria sprite", isOn: $showUnit)
                Toggle("Recovered cosmos background", isOn: $showBackground)
                if artwork(candidate) == nil {
                    Text("Research artwork unavailable. Run import_reveal_research.py and rebuild; production summons remain available.")
                        .foregroundStyle(.orange).accessibilityIdentifier("reveal-research-missing")
                }
                Text(candidate == "getglow" ? "Probable acquisition glow: ins_get references this cell twice with additive blend. Position and timing are not recovered." :
                    "Comparison candidate only. Starglow belongs to star-light presentation; stLight cells are flares, not proven ground platforms.")
                    .font(.caption)
                if let image = artwork(candidate) {
                    Image(uiImage: image).resizable().scaledToFit().frame(maxWidth: 280, maxHeight: 170)
                    Text("Uncomposited recovered cell: " + candidate).font(.caption)
                }
                Text("Source: Global-targeted preservation, exvius-data-010.zip / native/en/sd/gacha/Ver2_gachaeffect1.cpk. Not proof of retail Global CDN identity. No Memorial or third-party art is used here.")
                    .font(.caption2).foregroundStyle(.secondary)
            }.padding()
        }.navigationTitle("Character reveal research")
    }
}
