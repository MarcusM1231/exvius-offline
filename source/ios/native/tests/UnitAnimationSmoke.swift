import Foundation
@main struct UnitAnimationSmoke {
    static func main() {
        let ticks=[12,12,12,12]
        precondition(UnitAnimationClock.frame(at:0,ticks:ticks)==0)
        precondition(UnitAnimationClock.frame(at:0.2,ticks:ticks)==1)
        precondition(UnitAnimationClock.frame(at:0.799,ticks:ticks)==3)
        precondition(UnitAnimationClock.frame(at:0.8,ticks:ticks)==0)
        precondition(UnitAnimationClock.frame(at:800,ticks:ticks)==0)
        var clock=UnitAnimationClock();clock.advance(0.1);clock.paused=true;clock.advance(999)
        precondition(clock.elapsed==0.1);clock.paused=false;clock.speed=2;clock.advance(0.1)
        precondition(abs(clock.elapsed-0.3)<1e-8);clock.restart();precondition(clock.elapsed==0)
        clock.speed = .infinity;clock.advance(1);precondition(clock.elapsed==0)
        print("Unit animation timing passed")
    }
}
