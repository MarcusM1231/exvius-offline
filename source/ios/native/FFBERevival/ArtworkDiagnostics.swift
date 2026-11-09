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
            let expectedIDs=Set(catalog.units.filter {$0.value.artwork != nil}.map(\.key)).union(ExtraUnitArtwork.availableIDs).union(ExpandedUnitArtwork.availableIDs)
            guard Set(ids)==expectedIDs, declaredImages >= 3 else {
                throw APIError(message: "Bundled sprite count does not match the catalog")
            }
            let newSamples=(3...5).compactMap {rarity in ExpandedUnitArtwork.availableIDs.sorted().first {catalog.units[$0]?.rarity_code==rarity}}
            let renderIDs = Set(newSamples + Array(baseline.keys) + Array(ExtraUnitArtwork.availableIDs) + Array(ids.filter { baseline[$0] == nil }.prefix(4)))
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
            let missingID=ExpandedUnitArtwork.availableIDs.isEmpty ? "100004204":"100014405"
            guard catalog.artworkURL(masterID: missingID) == nil else {
                throw APIError(message: "Different form received a same-name sprite")
            }
            report = ["status": "passed", "named_ids": catalog.namedCount, "artwork_ids": catalog.artworkCount,
                      "rendered_units": rendered, "decoded_images": decoded, "missing_exact_form_has_no_art": true, "same_name_other_form_has_no_art": ExpandedUnitArtwork.availableIDs.isEmpty,
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
        }.padding().preferredColorScheme(.dark).task {
                status=ArtworkDiagnostics.run()
                let before=CrystalInspection.residentBytes();var peak=before;var rendered=0
                for id in ExpandedUnitArtwork.availableIDs.sorted().prefix(120) {
                    autoreleasepool {
                        let view=UnitArtworkView(unit:UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false))
                        if ImageRenderer(content:view).uiImage != nil {rendered += 1}
                        peak=max(peak,CrystalInspection.residentBytes())
                    }
                }
                let memory:[String:Any]=["rendered_requests":rendered,"resident_before":before,"resident_sampled_peak":peak,"resident_after":CrystalInspection.residentBytes(),"cache_count_target":64,"cache_cost_target_bytes":8*1024*1024,"campaign_accessed":false]
                if let base=try? FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true) {
                    let url=base.appendingPathComponent("FFBERevival/validation/unit-art-memory.json")
                    try? JSONSerialization.data(withJSONObject:memory,options:[.prettyPrinted,.sortedKeys]).write(to:url,options:.atomic)
                }
             }
    }
}

// Read-only visual evidence route. Preview identities are never saved or sent to a backend.
struct ExpandedArtDiagnostics:View {
    @State private var status="Checking expanded static artwork…"
    @State private var search=""
    private var ids:[String] {
        let primary=["206000504","100004104","100004105"]
        let expanded=ExpandedUnitArtwork.availableIDs.sorted {a,b in
            let ar=UnitCatalog.shared?.units[a]?.rarity_code ?? 0,br=UnitCatalog.shared?.units[b]?.rarity_code ?? 0
            return ar==br ? a<b:ar<br
        }
        return (primary+expanded+["100014405"]).filter {search.isEmpty || $0.contains(search) || (UnitCatalog.shared?.units[$0]?.name ?? "").localizedCaseInsensitiveContains(search)}
    }
    var body:some View {
        NavigationStack {
            List {
                Text("READ-ONLY ASSET CHECK · no summon or campaign changes").font(.caption).foregroundStyle(.purple)
                Text(status).font(.caption)
                ForEach(ids,id:\.self) {id in
                    NavigationLink {
                        StaticObtainedAssetPreview(masterID:id)
                    } label: {
                        UnitRowView(unit:UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false),inventoryDetail:"Tap for OBTAINED asset preview")
                    }
                }
            }.searchable(text:$search,prompt:"Name or exact master ID").navigationTitle("Expanded static sprites")
             .task {
                status=ArtworkDiagnostics.run()
                let before=CrystalInspection.residentBytes();var peak=before;var rendered=0
                for id in ExpandedUnitArtwork.availableIDs.sorted().prefix(120) {
                    autoreleasepool {
                        let view=UnitArtworkView(unit:UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false))
                        if ImageRenderer(content:view).uiImage != nil {rendered += 1}
                        peak=max(peak,CrystalInspection.residentBytes())
                    }
                }
                let memory:[String:Any]=["rendered_requests":rendered,"resident_before":before,"resident_sampled_peak":peak,"resident_after":CrystalInspection.residentBytes(),"cache_count_target":64,"cache_cost_target_bytes":8*1024*1024,"campaign_accessed":false]
                if let base=try? FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true) {
                    let url=base.appendingPathComponent("FFBERevival/validation/unit-art-memory.json")
                    try? JSONSerialization.data(withJSONObject:memory,options:[.prettyPrinted,.sortedKeys]).write(to:url,options:.atomic)
                }
             }
        }.preferredColorScheme(.dark)
    }
}
struct StaticObtainedAssetPreview:View {
    let masterID:String
    @Environment(\.dismiss) private var dismiss
    private var receipt:CommittedSummon {
        CommittedSummon(id:UUID(),bannerID:"asset-preview",offerID:"no-purchase",backendIdentity:"read-only-art",awards:[Award(instance_id:"asset-preview-"+masterID,unit_id:masterID,name:UnitCatalog.shared?.units[masterID]?.name,granted_rarity:UnitCatalog.shared?.units[masterID]?.rarity_code)])
    }
    var body:some View {
        SummonCharacterReveal(receipt:receipt) {_,_ in dismiss()}
            .overlay(alignment:.top) {Text("ASSET PREVIEW · NO SUMMON").font(.caption2).padding(5).background(.purple)}
    }
}
