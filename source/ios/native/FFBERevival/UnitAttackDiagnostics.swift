import SwiftUI
import UIKit

// Render-only fixtures exercise the exact production reveal, never transactions.
struct UnitAttackDiagnostics: View {
    @State private var receipt: CommittedSummon?
    @State private var controller: CharacterRevealController?
    @State private var label="ATTACK VALIDATION · RENDER-ONLY · NO CAMPAIGN"
    @State private var callbacks=0
    var body: some View {
        VStack(spacing:0) {
            Text(label).font(.caption2).padding(6).background(.purple)
            if let receipt,let controller {
                SummonCharacterReveal(receipt:receipt,controller:controller) {_,_ in callbacks += 1}.id(receipt.id)
            } else {Spacer();Text(label);Spacer()}
        }.task {await run()}
    }
    private struct Failure: Error {let message:String}
    @MainActor private func run() async {
        var root:URL?
        do {
            func require(_ value:Bool,_ text:String) throws {if !value {throw Failure(message:text)}}
            let folder=try FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true).appendingPathComponent("FFBERevival/validation/unit-attacks")
            try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true);root=folder
            var count=0,maximum=0;let before=CrystalInspection.residentBytes();var peak=before
            for entry in UnitAnimationLibrary.entries where entry.supported.contains("atk") {
                try autoreleasepool {
                    guard let clip=UnitAnimationClip.load(masterID:entry.master_id,kind:"atk") else {throw Failure(message:"Native attack rejected \(entry.master_id)")}
                    try require(clip.metadata.masterID==entry.master_id,"Exact-ID mismatch")
                    _=clip.image(at:0.3);count += 1
                    maximum=max(maximum,clip.metadata.width*clip.metadata.height*clip.images.count*4)
                    peak=max(peak,CrystalInspection.residentBytes())
                }
            }
            try require(count==UnitAnimationLibrary.entries.filter {$0.supported.contains("atk")}.count && count>0,"Native coverage differs from manifest")
            let ids=["202000203","100000103","206000103","206000113","100004604","205000703","100005404","213000504","100000102"]
            var cases:[[String:Any]]=[]
            for id in ids {
                label="PRODUCTION OBTAINED · \(id) · RENDER FIXTURE"
                let awards=[Award(instance_id:"fixture-"+id,unit_id:id,name:"Render-only fixture",granted_rarity:id=="100005404" || id=="100004604" ? 4 : 3)]
                let value=CommittedSummon(id:UUID(),bannerID:"render-only",offerID:"fixture",backendIdentity:"no-backend",awards:awards)
                let c=CharacterRevealController(receipt:value);controller=c;receipt=value;callbacks=0
                // The render-only launch can initially have an inactive ScenePhase.
                // Explicitly start this harness; real production still follows scene lifecycle.
                try await wait {c.hasStarted}
                c.resume()
                for (n,time) in [1.0,1.8,2.5,4.8].enumerated() {
                    try await wait {c.state.motionTime>=time || c.state.reason != nil}
                    try snapshot(folder.appendingPathComponent("\(id)-\(n).png"))
                }
                let attack=c.unitMotion.attack
                if let idle=c.unitMotion.idle {
                    for width in [320.0,402.0,768.0] {
                        let f=c.unitMotion.framing(width:width,height:360,baseline:300)
                        try require(f.anchor==0.5,"Production unit anchor is not centered")
                        try require(f.scale==ObtainedBodyFraming.scale(width:width,height:360,sourceWidth:idle.metadata.width,sourceHeight:idle.metadata.height),"Attack extent changed body scale")
                    }
                }
                if id=="100000102" {try require(c.animation==nil && c.sprite != nil,"Missing exact form did not use static fallback")}
                try require(c.unitMotion.sample(at:999)?.clip.metadata.kind != "atk","Attack did not return to idle")
                if let idle=c.unitMotion.idle {try require(c.unitMotion.sample(at:2,reducedMotion:true)?.clip === idle,"Reduced Motion changed clip")}
                c.suspend();let paused=c.state.motionTime
                try await Task.sleep(nanoseconds:120_000_000)
                try require(c.state.motionTime==paused,"Suspended reveal advanced")
                c.resume();try await wait {c.state.motionTime>paused}
                cases.append(["id":id,"attack":attack != nil,"idle":c.animation != nil,"static":c.sprite != nil,"attack_ticks":attack?.metadata.ticks.reduce(0,+) ?? 0])
                c.finish(.skipped);c.finish(.skipped);try require(callbacks==1,"Duplicate completion")
                try require(c.unitMotion.idle==nil && c.unitMotion.attack==nil,"Reveal retained decoded clips")
                controller=nil;receipt=nil
                try await Task.sleep(nanoseconds:50_000_000)
            }
            var released=0;let warmBefore=CrystalInspection.residentBytes()
            for _ in 0..<40 {
                weak var observed:ObtainedUnitMotion?
                autoreleasepool {
                    let motion=ObtainedUnitMotion();observed=motion;motion.load(masterID:"100004604")
                    _=motion.sample(at:1.2);_=motion.sample(at:999);motion.clear()
                }
                if observed==nil {released += 1}
            }
            let warmAfter=CrystalInspection.residentBytes()
            try require(released==40,"Motion owner retained")
            let report:[String:Any]=["status":"passed","native_loaded_attacks":count,"max_decoded_attack_bytes":maximum,"resident_before":before,"resident_sampled_peak":peak,"resident_warm_before":warmBefore,"resident_warm_after":warmAfter,"release_cycles":released,"cases":cases,"background_suspend":true,"reduced_motion":true,"finite_to_idle":true,"centered_idle_based_framing":true,"duplicate_completion_rejected":true,"backend_requests":0,"campaign_accessed":false]
            try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:folder.appendingPathComponent("report.json"));label="PASSED · FULL ATTACK LIBRARY / PRODUCTION RENDER FIXTURES"
        } catch {
            label="FAILED: \(error)"
            if let root {try? JSONSerialization.data(withJSONObject:["status":"failed","error":label,"phase":controller?.state.phase.rawValue ?? "none","time":controller?.state.motionTime ?? -1,"suspended":controller?.state.suspended ?? false,"ticking":controller?.isTicking ?? false]).write(to:root.appendingPathComponent("report.json"))}
        }
    }
    @MainActor private func wait(_ condition:() -> Bool) async throws {
        for _ in 0..<600 {if condition() {return};try await Task.sleep(nanoseconds:20_000_000)}
        throw Failure(message:"Playback timeout")
    }
    @MainActor private func snapshot(_ url:URL) throws {
        guard let window=UIApplication.shared.connectedScenes.compactMap({$0 as? UIWindowScene}).flatMap(\.windows).first(where:\.isKeyWindow) else {throw Failure(message:"No window")}
        let image=UIGraphicsImageRenderer(bounds:window.bounds).image {_ in window.drawHierarchy(in:window.bounds,afterScreenUpdates:true)}
        guard let data=image.pngData() else {throw Failure(message:"No PNG")};try data.write(to:url)
    }
}
