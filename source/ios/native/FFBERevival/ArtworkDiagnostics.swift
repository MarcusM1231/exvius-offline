import Foundation
import SwiftUI
import UIKit

@MainActor
enum ArtworkDiagnostics {
    static func run() -> String {
        var report: [String: Any] = [:]
        do {
            guard let catalog = UnitCatalog.shared else { throw APIError(message: "Missing unit catalog") }
            var rendered: [[String: Any]] = []
            let baseline = ["100004203": "Ludmille", "100000102": "Rain", "100000202": "Lasswell"]
            let ids = catalog.units.keys.sorted().filter { catalog.artworkURL(masterID: $0) != nil }
            let declaredImages = catalog.units.values.filter { $0.artwork != nil }.count
            let expectedIDs=Set(catalog.units.filter {$0.value.artwork != nil}.map(\.key)).union(ExtraUnitArtwork.availableIDs)
            guard Set(ids)==expectedIDs, declaredImages >= 3 else {
                throw APIError(message: "Bundled sprite count does not match the catalog")
            }
            let renderIDs = Set(Array(baseline.keys) + Array(ExtraUnitArtwork.availableIDs) + Array(ids.filter { baseline[$0] == nil }.prefix(4)))
            var decoded = 0
            for id in ids {
                let row = catalog.display(masterID: id, backendName: nil, rarity: nil, isAward: false)
                guard baseline[id] == nil || baseline[id] == row.name,
                      let url = row.artworkURL, let image = UIImage(contentsOfFile: url.path), image.size.width > 0 else {
                    throw APIError(message: "Metadata/image mismatch for " + id)
                }
                decoded += 1
                if renderIDs.contains(id) {
                    let renderer = ImageRenderer(content: UnitRowView(unit: row, inventoryDetail: "Read-only artwork check")
                        .padding().frame(width: 380).background(Color.white))
                    guard renderer.uiImage != nil else { throw APIError(message: "SwiftUI render failed for " + id) }
                    rendered.append(["unit_id": id, "name": row.name, "width": image.size.width,
                                     "height": image.size.height, "swiftui_rendered": true])
                }
            }
            guard catalog.artworkURL(masterID: "100004204") == nil else {
                throw APIError(message: "Different form received a same-name sprite")
            }
            report = ["status": "passed", "named_ids": catalog.namedCount, "artwork_ids": catalog.artworkCount,
                      "rendered_units": rendered, "decoded_images": decoded, "same_name_other_form_has_no_art": true,
                      "campaign_accessed": false, "network_used": false]
        } catch { report = ["status": "failed", "error": error.localizedDescription] }
        do {
            let folder = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                     appropriateFor: nil, create: true)
                .appendingPathComponent("FFBERevival/validation", isDirectory: true)
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: folder.appendingPathComponent("unit-artwork-report.json"), options: .atomic)
        } catch { return "Could not save artwork validation: " + error.localizedDescription }
        print("Artwork validation: \(report)")
        return String(describing: report["status"] ?? "failed")
    }
}

struct ExtraUnitArtDiagnostics:View {
    @State private var status="Checking exact static forms…"
    var body:some View {
        VStack(spacing:12) {
            Text("READ-ONLY STATIC FORM CHECK").font(.headline)
            Text(status).font(.caption)
            ForEach(["206000504","100004104","100004105"],id:\.self) {id in
                UnitRowView(unit:UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false),inventoryDetail:"Exact master ID \(id)")
            }
            Text("Original static artwork only · no animation or summon transaction").font(.caption)
        }.padding().preferredColorScheme(.dark).task {status=ArtworkDiagnostics.run()}
    }
}
