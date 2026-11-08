import SwiftUI
import UIKit

// Renderer fixtures are explicitly not awards and never call a backend or load a campaign.
struct UnitAnimationDiagnostics: View {
    @StateObject private var playback = UnitAnimationPreviewController()
    @State private var character: CharacterRevealController?
    @State private var receipt: CommittedSummon?
    @State private var label = "UNIT ANIMATION · RENDER-ONLY FIXTURES"
    @State private var reliable = false
    @State private var results: [Award] = []
    @State private var callbacks = 0
    var body: some View {
        VStack {
            Text(label).font(.caption2).padding(8).background(.purple)
            if let receipt, let character {
                SummonCharacterReveal(receipt:receipt,controller:character) { _,awards in callbacks += 1;results=awards }.id(receipt.id)
            } else if !results.isEmpty {
                GlobalSummonResults(awards:results,reliable:$reliable) {}
            } else if let clip=playback.clip {
                Text("\(clip.metadata.masterID) · \(clip.metadata.kind)")
                UnitAnimationView(clip:clip,elapsed:playback.clock.elapsed,scale:3).frame(height:360)
                Spacer()
            } else { Spacer();Text(label);Spacer() }
        }.foregroundStyle(.white).background(.black).task {await run()}
    }
    private struct Failure: Error {let message:String}
    @MainActor private func run() async {
        var folder:URL?
        do {
            func require(_ ok:Bool,_ text:String) throws {if !ok {throw Failure(message:text)}}
            let root=try FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true).appendingPathComponent("FFBERevival/validation/unit-animation")
            try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true);folder=root
            var counts:[String:Int]=[:]
            for uid in ["202000203","100000103","206000103","206000113","100008605","100009903","100011004"] {
                for kind in ( ["100008605","100009903","100011004"].contains(uid) ? ["idle"] : ["idle","standby"]) {
                    playback.load(uid,kind);guard let clip=playback.clip else {throw Failure(message:"Missing validated clip")}
                    try require(clip.metadata.masterID==uid,"Exact ID mismatch")
                    counts[uid+"-"+kind]=clip.images.count;playback.play()
                    try await Task.sleep(nanoseconds:1_300_000_000)
                    try snapshot(root.appendingPathComponent(uid+"-"+kind+".png"))
                    playback.pause();let paused=playback.clock.elapsed
                    try await Task.sleep(nanoseconds:100_000_000)
                    try require(playback.clock.elapsed==paused,"Paused clock advanced")
                }
            }
            playback.pause();playback.clip=nil
            let before=CrystalInspection.residentBytes()
            var peak=before, maxDecoded=0, loaded=0
            let entries=UnitAnimationLibrary.entries
            try require(entries.count==425 && entries.filter(\.is_target).count==423,"Gallery inventory mismatch")
            for entry in entries where entry.supported.contains("idle") {
                try autoreleasepool {
                    guard let clip=UnitAnimationClip.load(masterID:entry.master_id) else {throw Failure(message:"Native loader rejected \(entry.master_id)")}
                    try require(clip.metadata.masterID==entry.master_id,"Native exact ID mismatch")
                    maxDecoded=max(maxDecoded,clip.metadata.width*clip.metadata.height*clip.images.count*4)
                    _ = clip.image(at:0.5);peak=max(peak,CrystalInspection.residentBytes());loaded += 1
                }
            }
            let after=CrystalInspection.residentBytes()
            try require(UnitAnimationClip.load(masterID:"100000102")==nil,"Substituted another Rain form")
            try require(UnitAnimationClip.load(masterID:"100004203")==nil,"Unsupported unit acquired animation")
            let broken=root.appendingPathComponent("broken");try FileManager.default.createDirectory(at:broken,withIntermediateDirectories:true)
            try Data("bad".utf8).write(to:broken.appendingPathComponent("receipt.json"))
            try require(UnitAnimationClip.load(masterID:"202000203",directory:broken)==nil,"Corrupt resource accepted")
            var released=0
            for _ in 0..<40 {
                weak var weakClip:UnitAnimationClip?
                autoreleasepool {let clip=UnitAnimationClip.load(masterID:"202000203");weakClip=clip;_ = clip?.image(at:0.4)}
                if weakClip==nil {released += 1}
            }
            try require(released==40,"Clip retained between cycles")
            for count in [1,11] {
                let ids=["202000203","206000103","100004203","100000103","206000113"]
                let awards=(0..<count).map {Award(instance_id:"fixture-\($0)",unit_id:ids[$0%ids.count],name:"Renderer fixture",granted_rarity:3)}
                let frozen=CommittedSummon(id:UUID(),bannerID:"render-only",offerID:"fixture",backendIdentity:"no-backend",awards:awards)
                let control=CharacterRevealController(receipt:frozen);character=control;receipt=frozen;callbacks=0;results=[]
                for index in 0..<count {
                    for _ in 0..<200 {
                        if control.state.phase == .waitingForContinue {break}
                        try await Task.sleep(nanoseconds:20_000_000)
                    }
                    try require(control.state.phase == .waitingForContinue,"Reveal gate did not reach Continue")
                    try require(control.state.current?.unit_id==awards[index].unit_id,"Fixture order changed")
                    try require((control.animation != nil) == (ids[index%ids.count] != "100004203"),"Animation/static selection wrong")
                    if index==0 {try await Task.sleep(nanoseconds:900_000_000);try snapshot(root.appendingPathComponent("obtained-\(count).png"))}
                    if count==11 && index==2 {try snapshot(root.appendingPathComponent("static-fallback.png"))}
                    control.suspend();let position=control.state.motionTime
                    try await Task.sleep(nanoseconds:100_000_000)
                    try require(control.state.motionTime==position,"Reveal advanced while suspended");control.resume()
                    control.tap(expectedInstanceID:awards[index].instance_id)
                }
                try require(callbacks==1 && CommittedSummon.sameAwards(results,awards),"Continue changed results/callback count")
                try require(control.animation==nil,"Completed reveal retained animation")
                character=nil;receipt=nil
                try await Task.sleep(nanoseconds:250_000_000);try snapshot(root.appendingPathComponent("results-\(count).png"))
            }
            let a=[Award(instance_id:"skip",unit_id:"202000203",name:"Fixture",granted_rarity:3)]
            let frozen=CommittedSummon(id:UUID(),bannerID:"fixture",offerID:"fixture",backendIdentity:"no-backend",awards:a)
            let skip=CharacterRevealController(receipt:frozen);var done=0
            skip.onCompletion={_,returned in if CommittedSummon.sameAwards(a,returned) {done += 1}}
            skip.begin(active:false);skip.finish(.skipped);skip.finish(.skipped)
            try require(done==1 && skip.animation==nil,"Skip retained resources or repeated completion")
            let report:[String:Any]=["status":"passed","clips":counts,"native_loaded_idle_clips":loaded,"maximum_decoded_clip_bytes":maxDecoded,"resident_before_all_clips":before,"resident_sampled_peak":peak,"resident_after_all_clips":after,"exact_id_fallback":true,"corrupt_rejected":true,"release_cycles":released,"pause_resume":true,"single_and_eleven_continue":true,"skip_once":true,"backend_requests":0,"campaign_accessed":false,"timebase_retail_verified":false]
            try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:root.appendingPathComponent("report.json"));label="PASSED · renderer fixtures · no campaign access"
        } catch {
            label="FAILED: \(error)"
            if let folder {try? JSONSerialization.data(withJSONObject:["status":"failed","error":label]).write(to:folder.appendingPathComponent("report.json"))}
        }
    }
    @MainActor private func snapshot(_ url:URL) throws {
        guard let window=UIApplication.shared.connectedScenes.compactMap({$0 as? UIWindowScene}).flatMap(\.windows).first(where:\.isKeyWindow) else {throw Failure(message:"No window")}
        let image=UIGraphicsImageRenderer(bounds:window.bounds).image {_ in window.drawHierarchy(in:window.bounds,afterScreenUpdates:true)}
        guard let bytes=image.pngData() else {throw Failure(message:"No PNG")};try bytes.write(to:url)
    }
}
