import SwiftUI
import UIKit

struct UnitArtworkView: View {
    let unit: UnitDisplay
    var body: some View {
        Group {
            if let url = unit.artworkURL, let image = UIImage(contentsOfFile: url.path) {
                Image(uiImage: image).resizable().interpolation(.none).scaledToFit()
                    .accessibilityLabel("\(unit.name) pixel artwork")
                    .accessibilityIdentifier("unit-art-\(unit.masterID)")
            } else {
                VStack(spacing: 4) {
                    Image(systemName: "photo.badge.questionmark").font(.title2)
                    Text("Art unavailable").font(.caption2).multilineTextAlignment(.center)
                }
                .foregroundStyle(.secondary)
                .accessibilityLabel("Artwork unavailable for unit \(unit.masterID)")
                .accessibilityIdentifier("unit-art-missing-\(unit.masterID)")
            }
        }
        .frame(width: 88, height: 88)
    }
}

struct UnitRowView: View {
    let unit: UnitDisplay
    let inventoryDetail: String?
    var body: some View {
        HStack(spacing: 12) {
            UnitArtworkView(unit: unit)
            VStack(alignment: .leading, spacing: 4) {
                Text(unit.name).font(.headline)
                Text(unit.rarity)
                Text("ID \(unit.masterID)").font(.caption).foregroundStyle(.secondary)
                Text(unit.metadata).font(.caption2).foregroundStyle(.secondary)
                if let inventoryDetail { Text(inventoryDetail).font(.caption2).foregroundStyle(.secondary) }
            }
        }.padding(.vertical, 4)
    }
}

// Explicit visual test screen, never a summon and never writes inventory.
struct UnitArtworkPreview: View {
    @State private var validation = "Checking local artwork…"
    var body: some View {
        NavigationStack {
            List {
                Text("Asset verification only · these are not summon results.").font(.caption)
                Text("Validation: " + validation).font(.caption)
                ForEach(["100004203", "100000102", "100000202", "100004204"], id: \.self) { id in
                    UnitRowView(unit: UnitCatalog.display(masterID: id, backendName: nil, rarity: nil, isAward: false), inventoryDetail: nil)
                }
            }.navigationTitle("Artwork verification")
                .task { validation = ArtworkDiagnostics.run() }
        }
    }
}
