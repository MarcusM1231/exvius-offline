import SwiftUI
import UIKit
import CryptoKit

private struct ResearchBannerImage: Decodable {
    let role: String, file: String, provenance: String
    let width: Int, height: Int
}
private struct ResearchBannerOffer: Decodable {
    let label: String, price: String, guarantee: String
    let draws: Int
}
private struct ResearchBanner: Decodable, Identifiable {
    let id: String, name: String, tab: String, source: String, notice: String, ios_status: String
    let groups: [String], images: [ResearchBannerImage], offers: [ResearchBannerOffer], featured: [String], issues: [String]
    let visible: Bool
}
private struct ResearchBannerGroup: Decodable, Identifiable {let id: String, label: String}
private struct ResearchBannerCatalog: Decodable {let schema: Int;let read_only: Bool;let groups: [ResearchBannerGroup];let records: [ResearchBanner]}

private enum BannerResearchResources {
    static let expectedLock="521a29e3f1c58e7ffb285cc5adb0e7ca6045baa328f3c127c64a79d06a23c97f"
    static let root=Bundle.main.resourceURL?.appendingPathComponent("BannerResearch")
    static let hashes:[String:String] = {
        guard let root,let raw=try? Data(contentsOf:root.appendingPathComponent("receipt.json")),raw.count<100_000,
              let receipt=try? JSONSerialization.jsonObject(with:raw) as? [String:Any],receipt["lock_sha256"] as? String==expectedLock else {return [:]}
        return receipt["files"] as? [String:String] ?? [:]
    }()
    static func checked(_ name:String,maximum:Int)->Data? {
        guard let root,let data=try? Data(contentsOf:root.appendingPathComponent(name)),data.count<=maximum,
              hashes[name]==SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined() else {return nil}
        return data
    }
    static let catalog:ResearchBannerCatalog? = {
        guard let data=checked("catalog.json",maximum:2_000_000),let c=try? JSONDecoder().decode(ResearchBannerCatalog.self,from:data),c.schema==1,c.read_only,
              c.records.count<=5000,Set(c.records.map(\.id)).count==c.records.count else {return nil}
        return c
    }()
    static func image(_ asset:ResearchBannerImage,id:String)->UIImage? {
        guard !id.isEmpty,id.count<=10,id.allSatisfy({$0.isASCII && $0.isNumber}),["banner","detail_banner"].contains(asset.role),
              asset.file=="images/\(id)-\(asset.role).png",(1...2048).contains(asset.width),(1...2048).contains(asset.height),
              let data=checked(asset.file,maximum:512_000),let image=UIImage(data:data),image.cgImage?.width==asset.width,image.cgImage?.height==asset.height else {return nil}
        return image
    }
}
private struct ResearchBannerArt:View {
    let asset:ResearchBannerImage
    let id:String
    @State private var image:UIImage?
    var body:some View {
        Group {
            if let image {Image(uiImage:image).resizable().scaledToFit()}
            else {Text("Verified artwork unavailable").frame(maxWidth:.infinity,minHeight:70).background(.gray.opacity(0.15))}
        }.task(id:asset.file) {image=BannerResearchResources.image(asset,id:id)}
    }
}
struct BannerResearchPreview:View {
    @State private var search=ProcessInfo.processInfo.arguments.contains("--banner-research-global") ? "Rhus" : ""
    @State private var group="all"
    @State private var tab="all"
    @State private var verifiedOnly=true
    private var rows:[ResearchBanner] {
        (BannerResearchResources.catalog?.records ?? []).filter {r in
            r.visible && (!verifiedOnly || !r.images.isEmpty) && (group=="all" || r.groups.contains(group)) && (tab=="all" || r.tab==tab) && (search.isEmpty || r.id.contains(search) || r.name.localizedCaseInsensitiveContains(search))
        }
    }
    var body:some View {
        if ProcessInfo.processInfo.arguments.contains("--banner-research-detail"),
           let banner=BannerResearchResources.catalog?.records.first(where:{$0.id=="9200001"}) {
            BannerResearchDetails(banner:banner).preferredColorScheme(.dark)
        } else { browser }
    }
    private var browser:some View {
        List {
            Section {
                Text("READ-ONLY BANNER RESEARCH").font(.headline).foregroundStyle(.yellow)
                Text("Bundled Python catalog snapshot. No player, currency, inventory or purchase connection.").font(.caption)
                Text("Native research browser; not the completed original menu recreation.").font(.caption).foregroundStyle(.secondary)
                if let catalog=BannerResearchResources.catalog {
                    Text("\(catalog.records.count) definitions · \(catalog.records.filter(\.visible).count) archive entries · 4 verified image samples").font(.caption)
                    Picker("Archive group",selection:$group) {
                        Text("All groups").tag("all")
                        ForEach(catalog.groups) {Text($0.label).tag($0.id)}
                    }
                }
                Picker("Global tab",selection:$tab) {Text("All").tag("all");Text("Rare").tag("rare");Text("Standard").tag("standard");Text("Limited").tag("limited")}.pickerStyle(.segmented)
                Toggle("Verified image samples only",isOn:$verifiedOnly)
                Text("Season/Collab groups are the revival's browsing feature. No account eligibility is evaluated.").font(.caption)
            }
            if BannerResearchResources.catalog==nil {Text("Research bundle unavailable. Rebuild the optional banner research snapshot; production summons are unaffected.")}
            Section("\(rows.count) read-only entries") {
                ForEach(rows) {r in
                    NavigationLink {BannerResearchDetails(banner:r)} label: {
                        VStack(alignment:.leading,spacing:8) {
                            if let image=r.images.first(where:{$0.role=="banner"}) {ResearchBannerArt(asset:image,id:r.id)}
                            else {Text("Original banner artwork not recovered").font(.caption).foregroundStyle(.secondary)}
                            Text(r.name).font(.headline)
                            Text("\(r.id) · \(r.tab.capitalized)").font(.caption).monospacedDigit()
                            Text(r.images.first?.provenance ?? "Metadata only").font(.caption2).foregroundStyle(.secondary)
                            Text("\(r.offers.count) declared option(s) · details only").font(.caption)
                        }.padding(.vertical,4)
                    }
                }
            }
        }.navigationTitle("Banner research").searchable(text:$search,prompt:"Banner name or exact ID").preferredColorScheme(.dark)
    }
}
private struct BannerResearchDetails:View {
    let banner:ResearchBanner
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:16) {
                Text("READ ONLY · NO SUMMON ACTION").font(.headline).foregroundStyle(.yellow)
                Text(banner.name).font(.title2)
                Text("ID \(banner.id) · \(banner.tab.capitalized)").font(.caption)
                if let asset=banner.images.first(where:{$0.role=="detail_banner"}) ?? banner.images.first {
                    ResearchBannerArt(asset:asset,id:banner.id)
                    Text(asset.provenance).font(.caption)
                    if asset.role != "detail_banner" {Text("Calendar/list reference shown; original detail artwork not recovered.").font(.caption)}
                } else {Text("Exact detail artwork unavailable")}
                Text("Declared options — not live quotes").font(.headline)
                ForEach(Array(banner.offers.enumerated()),id:\.offset) {_,o in
                    VStack(alignment:.leading,spacing:4) {
                        Text("\(o.label) · \(o.draws) draw(s) · \(o.price)")
                        Text("Guarantee data: \(o.guarantee)").font(.caption)
                    }.padding(10).frame(maxWidth:.infinity,alignment:.leading).background(.gray.opacity(0.15))
                }
                ForEach(banner.issues,id:\.self) {Text($0).font(.caption).foregroundStyle(.orange)}
                Text(banner.notice).font(.caption)
                Text("Featured exact IDs: "+(banner.featured.isEmpty ? "not explicitly declared" : banner.featured.joined(separator:", "))).font(.caption)
                Text("Source: \(banner.source)").font(.caption)
                Text(banner.ios_status).font(.caption)
                Text("Actual eligibility, final rates, costs and rewards remain Python-owned. This page cannot buy anything.").font(.caption)
            }.padding()
        }.navigationTitle("Banner details").preferredColorScheme(.dark)
    }
}
