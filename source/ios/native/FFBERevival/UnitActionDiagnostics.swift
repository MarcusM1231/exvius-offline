import SwiftUI
import UIKit

struct UnitActionDiagnostics: View {
    @StateObject private var controller=UnitActionResearchController()
    @State private var label="DEVELOPER ACTION FIXTURES · NO CAMPAIGN"
    var body:some View {
        VStack {
            Text(label).font(.caption).padding().background(.purple)
            if let clip=controller.clip {
                GeometryReader {geometry in
                    UnitAnimationView(clip:clip,elapsed:controller.sample.localTime,scale:scale(width:geometry.size.width)).frame(height:300)
                }.frame(height:350)
                Text("\(controller.masterID) · \(controller.currentAction) · frame \(UnitAnimationClock.frame(at:controller.sample.localTime,ticks:clip.metadata.ticks)+1)").font(.caption)
            }
            Text(controller.explanation).font(.caption).padding()
            Spacer()
        }.background(Color(red:0.05,green:0.06,blue:0.1)).foregroundStyle(.white).task {await run()}
    }
    private func scale(width:Double)->Double {
        let values=Array((UnitActionLibrary.catalog[controller.masterID] ?? [:]).values)
        let reach=values.map {max($0.anchor[0],$0.width-$0.anchor[0])}.max() ?? 1
        let up=values.map(\.anchor).map {$0[1]}.max() ?? 1
        return min(2,min(width*0.46/Double(max(1,reach)),290/Double(max(1,up))))
    }
    private struct Failure:Error {let message:String}
    @MainActor private func run() async {
        var folder:URL?
        do {
            func require(_ ok:Bool,_ why:String) throws {if !ok {throw Failure(message:why)}}
            let root=try FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true).appendingPathComponent("FFBERevival/validation/unit-actions")
            try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true);folder=root
            var validated=0;let memoryBefore=CrystalInspection.residentBytes();var peak=memoryBefore
            for id in UnitActionLibrary.ids {
                for kind in UnitActionLibrary.kinds where UnitActionLibrary.catalog[id]?[kind] != nil {
                    try autoreleasepool {
                        guard let clip=UnitActionLibrary.clip(id,kind) else {throw Failure(message:"Native action loader failed \(id)/\(kind)")}
                        try require(clip.metadata.masterID==id && clip.metadata.kind==kind,"Native action identity mismatch")
                        validated += 1;peak=max(peak,CrystalInspection.residentBytes())
                    }
                }
            }
            try require(validated==34,"Unexpected playable action coverage")
            var cases:[[String:Any]]=[]
            for kind in UnitActionLibrary.kinds {
                label="CHIZURU · \(UnitActionLibrary.title(kind)) · ONCE"
                controller.configure(id:"100004604",actions:[kind]);guard let plan=controller.plan else {throw Failure(message:"Missing Chizuru action")}
                try await wait {controller.driver.clock.elapsed>=plan.duration*0.4}
                try snapshot(root.appendingPathComponent(kind+"-mid.png"))
                try await wait {controller.sample.completed}
                try require(controller.completedCount==1,"Finite action completion repeated")
                controller.update(plan.duration+999);try require(controller.completedCount==1,"Late tick completed twice")
                try snapshot(root.appendingPathComponent(kind+"-end.png"))
                cases.append(["kind":kind,"duration":plan.duration,"completion_count":controller.completedCount])
            }
            for preset in UnitActionPreset.allCases {
                label="EXPERIMENTAL \(preset.label) · NOT ORIGINAL ROUTING"
                controller.configure(id:"100004604",actions:preset.actions)
                guard let plan=controller.plan else {throw Failure(message:"Missing preset action")}
                try await wait {controller.driver.clock.elapsed>=plan.duration*0.45}
                try snapshot(root.appendingPathComponent(preset.rawValue+"-sequence.png"))
                try await wait {controller.sample.completed}
                try require(controller.completedCount==1,"Preset completion repeated")
            }
            controller.configure(id:"202000203",actions:["atk","idle"])
            try await wait {controller.driver.clock.elapsed>0.15};controller.pause();let paused=controller.driver.clock.elapsed
            controller.suspend();controller.resumeIfRequested()
            try await Task.sleep(nanoseconds:150_000_000)
            try require(controller.driver.clock.elapsed==paused,"User paused selection resumed unexpectedly")
            controller.play();try await wait {controller.driver.clock.elapsed>paused+0.1}
            controller.driver.clock.speed=2;controller.restart()
            try require(controller.driver.clock.elapsed==0,"Restart did not reset position")
            controller.stop();try require(controller.clip==nil && controller.plan==nil,"Cancel retained preview")
            controller.configure(id:"206000113",actions:UnitActionPreset.attackIdle.actions)
            try require(controller.plan==nil && controller.clip?.metadata.kind=="idle","Missing attack did not fall back safely")
            controller.stop()
            let broken=root.appendingPathComponent("broken");try FileManager.default.createDirectory(at:broken,withIntermediateDirectories:true)
            try Data("bad".utf8).write(to:broken.appendingPathComponent("receipt.json"))
            try require(UnitActionLibrary.clip("100004604","atk",directory:broken)==nil,"Corrupt action accepted")
            var released=0
            for _ in 0..<40 {
                weak var observed:UnitActionResearchController?
                autoreleasepool {
                    let c=UnitActionResearchController();observed=c;c.configure(id:"100004604",actions:["atk","idle"]);c.update(999);c.update(1000)
                }
                if observed==nil {released += 1}
            }
            try require(released==40,"Preview controller retained")
            try await Task.sleep(nanoseconds:200_000_000)
            let warmBefore=CrystalInspection.residentBytes();var warmReleased=0
            for _ in 0..<40 {
                weak var observed:UnitActionResearchController?
                autoreleasepool {
                    let c=UnitActionResearchController();observed=c;c.configure(id:"100004604",actions:["atk","idle"]);c.update(999);c.stop()
                }
                if observed==nil {warmReleased += 1}
            }
            let warmAfter=CrystalInspection.residentBytes();peak=max(peak,max(warmBefore,warmAfter))
            try require(warmReleased==40,"Warm preview controller retained")
            let report:[String:Any]=["status":"passed","validated_actions":validated,"individual_finite_cases":cases,"experimental_presets":5,"pause_resume":true,"restart_and_speed":true,"missing_action_idle_fallback":true,"corrupt_rejected":true,"released_controllers":released,"warm_release_cycles":warmReleased,"resident_warm_before":warmBefore,"resident_warm_after":warmAfter,"resident_before":memoryBefore,"resident_sampled_peak":peak,"resident_after":CrystalInspection.residentBytes(),"backend_requests":0,"campaign_accessed":false,"production_idle_changed":false]
            try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:root.appendingPathComponent("report.json"));label="PASSED · ACTION RESEARCH · NO CAMPAIGN"
        } catch {
            label="FAILED \(error)"
            if let folder {try? JSONSerialization.data(withJSONObject:["status":"failed","error":label]).write(to:folder.appendingPathComponent("report.json"))}
        }
    }
    @MainActor private func wait(_ predicate:()->Bool) async throws {
        for _ in 0..<600 {if predicate() {return};try await Task.sleep(nanoseconds:20_000_000)}
        throw Failure(message:"Action playback timed out")
    }
    @MainActor private func snapshot(_ url:URL) throws {
        guard let window=UIApplication.shared.connectedScenes.compactMap({$0 as? UIWindowScene}).flatMap(\.windows).first(where:\.isKeyWindow) else {throw Failure(message:"No window")}
        let image=UIGraphicsImageRenderer(bounds:window.bounds).image {_ in window.drawHierarchy(in:window.bounds,afterScreenUpdates:true)}
        guard let data=image.pngData() else {throw Failure(message:"No snapshot")};try data.write(to:url)
    }
}
