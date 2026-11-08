import Foundation

// Reuses exact-ID production clips, never the Developer research bundle.
// At most the current unit's idle and attack are decoded. No frame-time IO.
@MainActor final class ObtainedUnitMotion {
    private(set) var idle: UnitAnimationClip?
    private(set) var attack: UnitAnimationClip?
    private(set) var policy = ObtainedActionPolicy()
    func load(masterID: String, includeAttackWithoutIdle: Bool = false) {
        clear()
        policy = .originalStyle(masterID: masterID)
        idle = UnitAnimationClip.load(masterID: masterID)
        if idle != nil || includeAttackWithoutIdle { attack = UnitAnimationClip.load(masterID: masterID,kind: "atk") }
    }
    func sample(at time: Double, reducedMotion: Bool = false) -> (clip: UnitAnimationClip,time: Double)? {
        guard let idle else {return nil}
        if reducedMotion {return (idle,0)}
        let sample=policy.sample(at:time,attackTicks:attack?.metadata.ticks,idleTicks:idle.metadata.ticks)
        return (sample.kind == "atk" ? (attack ?? idle) : idle,sample.time)
    }
    func framing(width: Double, height: Double, baseline: Double, fitEffects: Bool = false) -> (scale: Double, anchor: Double) {
        if !fitEffects, let idle {
            return (ObtainedBodyFraming.scale(width:width,height:height,sourceWidth:idle.metadata.width,sourceHeight:idle.metadata.height),0.5)
        }
        let clips=[idle,attack].compactMap {$0}
        let left=Double(max(1,clips.map {$0.metadata.anchor[0]}.max() ?? 1))
        let right=Double(max(1,clips.map {$0.metadata.width-$0.metadata.anchor[0]}.max() ?? 1))
        let up=Double(max(1,clips.map {$0.metadata.anchor[1]}.max() ?? 1))
        let down=Double(max(1,clips.map {$0.metadata.height-$0.metadata.anchor[1]}.max() ?? 1))
        // Fit the full source-space union, using the whole stage rather than the
        // old 65% width. Anchor/scale remain fixed through all action changes.
        let scale=min(3.2,min(width*0.94/(left+right),min(baseline*0.96/up,max(1,height-baseline)*0.96/down)))
        let anchor=(width-(left+right)*scale)/2+left*scale
        return (scale,anchor/max(1,width))
    }
    func clear() {idle=nil;attack=nil}
}
