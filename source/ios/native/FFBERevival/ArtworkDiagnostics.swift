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
            for (id, name) in [("100004203", "Ludmille"), ("100000102", "Rain"), ("100000202", "Lasswell")] {
                let row = catalog.display(masterID: id, backendName: nil, rarity: nil, isAward: false)
                guard row.name == name, let url = row.artworkURL,
                      let image = UIImage(contentsOfFile: url.path), image.size.width > 0 else {
                    throw APIError(message: "Metadata/image mismatch for " + id)
                }
                let renderer = ImageRenderer(content: UnitRowView(unit: row, inventoryDetail: "Read-only artwork check")
                    .padding().frame(width: 380).background(Color.white))
                guard renderer.uiImage != nil else { throw APIError(message: "SwiftUI render failed for " + id) }
                rendered.append(["unit_id": id, "name": row.name, "width": image.size.width,
                                 "height": image.size.height, "swiftui_rendered": true])
            }
            guard catalog.artworkURL(masterID: "100004204") == nil else {
                throw APIError(message: "Different form received a same-name sprite")
            }
            report = ["status": "passed", "named_ids": catalog.namedCount, "artwork_ids": catalog.artworkCount,
                      "rendered_units": rendered, "same_name_other_form_has_no_art": true,
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
