import Foundation
@main struct UnitActionSequenceSmoke {
    static func main() throws {
        let available=["idle":[12,12,12,12],"standby":[6,6,6,6],"atk":[5,5,10],"magic_atk":[8,8],"win_before":[6,6],"win":[6,6,6,6]]
        for preset in UnitActionPreset.allCases {
            let plan=try UnitActionPlan(actions:preset.actions,available:available)
            var t=0.0
            for (i,segment) in plan.segments.enumerated() {
                precondition(plan.sample(at:t).segment==i)
                precondition(!plan.sample(at:t).completed)
                precondition(plan.sample(at:t+segment.duration/2).segment==i)
                t += segment.duration
            }
            let end=plan.sample(at:plan.duration)
            precondition(end.completed && end.segment==preset.actions.count-1)
            precondition(end.localTime < plan.segments.last!.duration)
            precondition(UnitAnimationClock.frame(at:end.localTime,ticks:plan.segments.last!.ticks)==plan.segments.last!.ticks.count-1)
            precondition(plan.sample(at:plan.duration+999)==end)
            let repeatPlan=try UnitActionPlan(actions:preset.actions,available:available,repeats:true)
            precondition(repeatPlan.sample(at:repeatPlan.duration).segment==0 && !repeatPlan.sample(at:repeatPlan.duration).completed)
        }
        let hold=try UnitActionPlan(actions:["atk","idle"],available:available,hold:0.5)
        precondition(hold.sample(at:1.0/3+0.1).holding)
        precondition(hold.sample(at:1.0/3+0.5).segment==1)
        do {_ = try UnitActionPlan(actions:["unknown"],available:available);preconditionFailure()} catch UnitActionPlan.PlanError.missing("unknown") {}
        for invalid in [[],[0],[601],[-1]] as [[Int]] {
            do {_ = try UnitActionPlan(actions:["atk"],available:["atk":invalid]);preconditionFailure()} catch {}
        }
        var clock=UnitAnimationClock();clock.advance(0.1);clock.paused=true;clock.advance(1000);precondition(clock.elapsed==0.1)
        clock.paused=false;clock.speed=2;clock.advance(0.1);precondition(abs(clock.elapsed-0.3)<1e-8)
        clock.restart();precondition(clock.elapsed==0)
        print("Finite actions, presets, boundaries, explicit holds/repeats, missing actions, pause/speed/restart passed")
    }
}
