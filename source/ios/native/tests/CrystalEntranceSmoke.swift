import Foundation
@main struct CrystalEntranceSmoke {
    static func main() {
        var clock = TapSummonClock()
        precondition(clock.phase == .fallingCrystals && !clock.showsTouchPrompt && !clock.tap())
        clock.advance(1.0)
        precondition(clock.phase == .fallingCrystals)
        let visible = (0..<(CrystalEntranceTiming.count-1)).filter { FallingCrystalPose.sample(index:$0,time:1).visible }
        precondition(visible.count >= 2)
        for i in visible {
            let a = FallingCrystalPose.sample(index:i,time:1), b = FallingCrystalPose.sample(index:i,time:1.01)
            precondition(b.y<a.y && a.scale>0 && a.opacity<=1 && a.opacity>=0)
            precondition(a.x.isFinite && a.z.isFinite && a.roll.isFinite)
        }
        clock.suspend();let elapsed=clock.elapsed,motion=clock.motionTime
        clock.advance(99);precondition(clock.elapsed==elapsed && clock.motionTime==motion && !clock.tap())
        clock.resume();clock.advance(CrystalEntranceTiming.fallingDuration-1)
        precondition(clock.phase == .arriving && !clock.showsTouchPrompt && !clock.tap())
        clock.advance(CrystalEntranceTiming.arrivalDuration)
        precondition(clock.phase == .waitingForTap && clock.showsTouchPrompt)
        for _ in 0..<1000 { clock.advance(1000);precondition(clock.phase == .waitingForTap && clock.showsTouchPrompt) }
        precondition(clock.tap() && !clock.showsTouchPrompt)
        for _ in 0..<50 {precondition(!clock.tap())}
        clock.advance(1.2);precondition(clock.phase == .revealing && !clock.showsTouchPrompt)
        precondition(clock.advance(0.4) && clock.phase == .finished && !clock.showsTouchPrompt)
        precondition(!clock.advance(99))
        var old = TapSummonClock(includeFalling:false);precondition(old.phase == .arriving)
        old.advance(0.9);precondition(old.phase == .waitingForTap && old.showsTouchPrompt)
        var exact = TapSummonClock();exact.advance(CrystalEntranceTiming.totalArrival)
        precondition(exact.phase == .waitingForTap)
        precondition(!FallingCrystalPose.sample(index:99,time:1).visible && !FallingCrystalPose.sample(index:0,time:.nan).visible)
        print("Falling entrance, prompt phase, pause/tap/once-only and legacy-arrival contracts passed")
    }
}
