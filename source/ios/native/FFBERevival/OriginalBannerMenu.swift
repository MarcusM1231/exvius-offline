import SwiftUI
import UIKit
import CryptoKit
import ImageIO

// Width-scaled original regions, not a stretched 640x1136 screenshot. SwiftUI
// supplies safe areas; only decorative art can extend beyond the content region.

final class OriginalMenuResources {
    static let shared = OriginalMenuResources()
    let ui = SummonUIResources(directory: Bundle.main.resourceURL?.appendingPathComponent("GlobalMenu"))
    struct Art: Decodable { let file: String, provenance: String; let width: Int, height: Int }
    private let root = Bundle.main.resourceURL?.appendingPathComponent(ProcessInfo.processInfo.arguments.contains("--banner-art-missing") ? "BannerArt-Missing":"BannerArt")
    private let cache = NSCache<NSString,UIImage>()
    private var files: [String:String] = [:]
    private(set) var catalog: [String:[String:Art]] = [:]
    init() {
        cache.countLimit=16; cache.totalCostLimit=12*1024*1024
        guard let root,let data=try? Data(contentsOf:root.appendingPathComponent("receipt.json")),
              let receipt=try? JSONSerialization.jsonObject(with:data) as? [String:Any],
              receipt["lock_sha256"] as? String == Self.artLock,
              let hashes=receipt["files"] as? [String:String] else { return }
        files=hashes
        if let body=checked("catalog.json",limit:2_000_000) { catalog=(try? JSONDecoder().decode([String:[String:Art]].self,from:body)) ?? [:] }
    }
    // Replaced only after a checksum-verified import, never a runtime URL.
    static let artLock = "170dd21741a3c6eb29d0021a77f988ec1009d92f9a0b8e4aeed705c6a93c6e1a"
    private func checked(_ file: String,limit:Int) -> Data? {
        guard let root,!file.contains(".."),let data=try? Data(contentsOf:root.appendingPathComponent(file)),data.count<=limit,
              files[file]==SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined() else {return nil}
        return data
    }
    func art(_ id:String,detail:Bool)->Art? { catalog[id]?[detail ? "detail_banner":"banner"] ?? catalog[id]?["banner"] }
    func image(_ id:String,detail:Bool,role:String?=nil)->UIImage? {
        guard !id.isEmpty,id.count<=10,id.allSatisfy({$0.isASCII && $0.isNumber}),
              let a=role.flatMap({catalog[id]?[$0]}) ?? art(id,detail:detail),
              let expected=files[a.file],expected.count==64,a.file=="images/\(expected).png",
              a.width>0,a.height>0,max(a.width,a.height)<=4096 else {return nil}
        if let im=cache.object(forKey:a.file as NSString) {return im}
        guard let data=checked(a.file,limit:2_000_000),let source=CGImageSourceCreateWithData(data as CFData,nil),
              let properties=CGImageSourceCopyPropertiesAtIndex(source,0,nil) as? [CFString:Any],
              properties[kCGImagePropertyPixelWidth] as? Int==a.width,properties[kCGImagePropertyPixelHeight] as? Int==a.height else {return nil}
        let options:[CFString:Any]=[kCGImageSourceCreateThumbnailFromImageAlways:true,kCGImageSourceCreateThumbnailWithTransform:true,kCGImageSourceThumbnailMaxPixelSize:min(1024,max(a.width,a.height)),kCGImageSourceShouldCacheImmediately:true]
        guard let cg=CGImageSourceCreateThumbnailAtIndex(source,0,options as CFDictionary) else {return nil}
        let im=UIImage(cgImage:cg)
        cache.setObject(im,forKey:a.file as NSString,cost:cg.bytesPerRow*cg.height);return im
    }
    func extraRoles(_ id:String)->[String] {(catalog[id]?.keys.filter {$0.hasPrefix("detail_extra_")} ?? []).sorted()}

}
struct OriginalMenuArt:View {
    let id:String
    var body:some View {
        if let image=OriginalMenuResources.shared.ui.image(id) {Image(uiImage:image).resizable().interpolation(.none)}
        else {Color(red:0.04,green:0.08,blue:0.19).overlay(Text("Artwork unavailable").font(.caption))}
    }
}
struct OriginalMenuButton:View {
    let title:String
    var enabled=true
    let action:()->Void
    var body:some View {
        Button(action:action) {
            Text(title).font(.system(size:16,weight:.bold,design:.serif)).foregroundStyle(.white).shadow(color:.black,radius:1)
                .frame(maxWidth:.infinity,minHeight:44).background {OriginalMenuArt(id:"small-button")}
        }.buttonStyle(.plain).disabled(!enabled).opacity(enabled ? 1:0.45)
    }
}
struct ExactBannerArt:View {
    let id:String
    let name:String
    var detail=false
    var role:String? = nil
    @State private var image:UIImage?
    var body:some View {
        Group {
            if let image {Image(uiImage:image).resizable().interpolation(.none).scaledToFit()}
            else {
                ZStack {
                    OriginalMenuArt(id:"background-top")
                    VStack(spacing:8) {Text(name).font(.system(size:23,weight:.bold,design:.serif));Text("Banner artwork unavailable").font(.system(size:16))}.multilineTextAlignment(.center).padding(20)
                }.aspectRatio(4,contentMode:.fit)
            }
        }.task(id:id+String(detail)+(role ?? "")) {image=OriginalMenuResources.shared.image(id,detail:detail,role:role)}.onDisappear {image=nil}
    }
}
struct OriginalBannerMenu:View {
    @ObservedObject var model:SummonModel
    var initialID:String? = nil
    let choose:(Banner,Offer) async -> Void
    let latest:()->Void
    @State private var category="rare"
    @State private var archive="all"
    @State private var selectedID:String?
    @State private var search=""
    @State private var filterOpen=false
    private var selected:MenuBanner? {model.menuCatalog?.banners.first(where:{$0.id==selectedID})}
    private var rows:[MenuBanner] {(model.menuCatalog?.banners ?? []).filter { $0.category==category && (archive=="all" || $0.groups.contains(archive) || $0.playable) && (search.isEmpty || $0.name.localizedCaseInsensitiveContains(search) || $0.id.contains(search)) }}
    var body:some View {
        GeometryReader { geometry in
            let metrics=GlobalMenuMetrics(width:geometry.size.width)
            VStack(spacing:0) {
                HStack(spacing:6) {
                    OriginalMenuButton(title:selected == nil ? "Archive":"Back") {if selected != nil {selectedID=nil} else {filterOpen=true}}
                    Text(selected == nil ? "":"DETAILS").font(.system(size:21,weight:.bold,design:.serif)).foregroundStyle(.white).frame(maxWidth:.infinity)
                    OriginalMenuButton(title:"Results",enabled:!model.results.isEmpty && !model.busy,action:latest)
                }.frame(height:48).background {OriginalMenuArt(id:"line")}
                if let selected {detail(selected,width:metrics.bannerWidth)}
                else {
                    HStack(spacing:0) {
                        ForEach([("rare","pay","Rare"),("standard","free","Standard"),("limited","limited","Limited")],id:\.0) { tab in
                            Button {category=tab.0} label: {
                                OriginalMenuArt(id:"tab-\(tab.1)-\(category==tab.0 ? 1:2)")
                                    .scaledToFit().frame(maxWidth:.infinity,minHeight:44)
                            }.buttonStyle(.plain).accessibilityLabel(tab.2).accessibilityIdentifier("global-tab-\(tab.0)")
                        }
                    }.frame(height:metrics.tabHeight).background {OriginalMenuArt(id:"tabs")}
                    if let error=model.menuError {Text(error).font(.caption).padding()}
                    if model.menuCatalog==nil {ProgressView("Loading banners…").tint(.white).padding()}
                    ScrollView {
                        LazyVStack(spacing:12*metrics.scale) {
                            if rows.isEmpty && model.menuCatalog != nil {Text("No banners in this category or archive filter.").padding(25)}
                            ForEach(rows) {b in
                                Button {selectedID=b.id} label: {
                                    VStack(spacing:0) {
                                        ExactBannerArt(id:b.id,name:b.name)
                                        HStack {Text(b.name).lineLimit(2);Spacer();Text(b.playable ? "Details":"Unavailable")}
                                            .font(.system(size:max(12,20*metrics.scale),design:.serif)).padding(.horizontal,10).padding(.vertical,6)
                                            .background {OriginalMenuArt(id:"window")}
                                    }
                                }.buttonStyle(.plain).accessibilityIdentifier("global-banner-\(b.id)")
                            }
                        }.padding(.top,10).padding(.bottom,16).frame(maxWidth:metrics.bannerWidth)
                            .frame(maxWidth:.infinity)
                    }.background {OriginalMenuArt(id:"background-top").scaledToFill().clipped()}
                }
            }.frame(maxWidth:640).frame(maxWidth:.infinity)
        }.foregroundStyle(.white)
        .sheet(isPresented:$filterOpen) {
            VStack(spacing:18) {
                Text("Offline archive filter").font(.title2)
                Text("Revival browsing groups; the main tabs follow Global categories.").font(.caption)
                Picker("Archive",selection:$archive) {Text("All banners").tag("all");ForEach(model.menuCatalog?.groups ?? []) {Text($0.label).tag($0.id)}}.pickerStyle(.wheel)
                TextField("Search name or banner ID",text:$search).textFieldStyle(.roundedBorder)
                OriginalMenuButton(title:"Done") {filterOpen=false}
            }.padding(24).background {OriginalMenuArt(id:"window")}.preferredColorScheme(.dark)
        }.onAppear {
            if let initialID {selectedID=initialID}
            let args=ProcessInfo.processInfo.arguments
            for tab in ["rare","standard","limited"] where args.contains("--menu-"+tab) {category=tab}
            if model.results.isEmpty, let i=args.firstIndex(of:"--menu-banner"),args.count>i+1 {selectedID=args[i+1]}
        }
    }
    private func detail(_ b:MenuBanner,width:Double)->some View {
        ScrollView {
            LazyVStack(spacing:14) {
                ExactBannerArt(id:b.id,name:b.name,detail:true)
                Text(b.name).font(.system(size:23,weight:.bold,design:.serif)).multilineTextAlignment(.center).padding(.horizontal,12)
                if b.playable {Text("Historical artwork · unit rewards only. Available offline offers are shown below.").font(.caption).multilineTextAlignment(.center).padding(.horizontal,16)}
                if !b.playable {Text(b.availability).font(.callout).foregroundStyle(.yellow).padding(.horizontal,16)}
                if !b.description.isEmpty {Text(b.description).padding(.horizontal,16)}
                if b.playable,let banner=model.banners.first(where:{$0.id==b.id}) {
                    HStack(alignment:.top,spacing:0) {
                        ForEach(b.offers) { q in
                            VStack(spacing:10) {
                                SummonOfferButton(offer:q.transactionOffer,enabled:q.eligible && !model.busy && !model.needsRefresh) {Task {await choose(banner,q.transactionOffer)}}
                                    .scaleEffect(min(1,width/640)).frame(width:width/2,height:136*min(1,width/640))
                                Text(q.guarantee).font(.system(size:13)).multilineTextAlignment(.center).padding(.horizontal,8)
                                if !q.reason.isEmpty {Text(q.reason).font(.caption).foregroundStyle(.yellow)}
                            }.frame(width:width/2)
                        }
                    }
                    if b.offers.contains(where:{!$0.ticket_group.isEmpty}) {Text("Ticket purchases are not yet available.").font(.caption)}
                }
                ForEach(b.offers.filter {_ in !b.playable}) {q in
                    VStack(spacing:8) {
                        Text("Summon ×\(q.draws) · \(q.cost.label)").font(.headline)
                        OriginalMenuButton(title:"Unavailable",enabled:false) {}.frame(maxWidth:250)
                        Text(q.guarantee).font(.callout)
                        if !q.reason.isEmpty {Text(q.reason).font(.caption).foregroundStyle(.yellow)}
                        if q.steps>0 {Text("Step \(q.step) of \(q.steps) · Lap \(q.lap)").font(.caption)}
                        if !q.ticket_group.isEmpty {Text(q.tickets.isEmpty ? "Ticket data unavailable · ticket purchases disabled":"Tickets held: \(q.tickets.reduce(0){$0+$1.balance}) · ticket purchases disabled").font(.caption)}
                        if q.purchase_limit>0 {Text("Used \(q.usage) / \(q.purchase_limit)").font(.caption)}
                    }.multilineTextAlignment(.center).padding(.horizontal,16)
                }
                if !b.featured.isEmpty {
                    Text("FEATURED UNITS").font(.system(.headline,design:.serif))
                    ForEach(Array(b.featured.prefix(12)),id:\.self) {id in
                        let unit=UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false)
                        HStack {UnitArtworkView(unit:unit).frame(width:64,height:70);Text(unit.name);Spacer()}.padding(.horizontal,20)
                    }
                }
                ForEach(OriginalMenuResources.shared.extraRoles(b.id),id:\.self) {role in
                    ExactBannerArt(id:b.id,name:b.name,detail:true,role:role)
                }
                Text("SUMMON RATES").font(.system(.headline,design:.serif))
                ForEach(Array(b.rates.enumerated()),id:\.offset) {_,r in Text("\(r.rarity)★ pool weight: \(String(format:"%.3g",r.weight*100))%").font(.callout)}
                Text(b.notice).font(.caption).padding(.horizontal,18)
                if let art=OriginalMenuResources.shared.art(b.id,detail:true),art.provenance.hasPrefix("community") {Text("Archived community banner image").font(.caption2).foregroundStyle(.secondary)}
                OriginalMenuButton(title:"Back to banners") {selectedID=nil}.frame(maxWidth:260).padding(.bottom,20)
            }.frame(maxWidth:width).frame(maxWidth:.infinity)
        }.background {OriginalMenuArt(id:"background-top").scaledToFill().clipped()}
    }
}
