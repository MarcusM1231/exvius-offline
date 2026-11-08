import Foundation

enum UnitActionPreset: String, CaseIterable {
    case current, attackStandby, attackIdle, victory, standbyVictory
    var actions: [String] {
        switch self {
        case .current: return ["idle","idle"]
        case .attackStandby: return ["atk","standby","atk","standby"]
        case .attackIdle: return ["atk","idle","atk","idle"]
        case .victory: return ["win_before","win","idle"]
        case .standbyVictory: return ["standby","win_before","win"]
        }
    }
    var label: String {
        switch self {
        case .current: return "A · idle → idle"
        case .attackStandby: return "B · attack → standby ×2"
        case .attackIdle: return "C · attack → idle ×2"
        case .victory: return "D · victory entrance → victory → idle"
        case .standbyVictory: return "E · standby → victory entrance → victory"
        }
    }
}
struct UnitActionSegment: Equatable {
    let kind: String
    let ticks: [Int]
    var duration: Double {Double(ticks.reduce(0,+))/60}
}
struct UnitActionSample: Equatable {
    let segment: Int
    let localTime: Double
    let completed: Bool
    let holding: Bool
}
struct UnitActionPlan {
    let segments: [UnitActionSegment]
    let hold: Double
    let repeats: Bool
    init(actions: [String], available: [String:[Int]], hold: Double = 0, repeats: Bool = false) throws {
        guard !actions.isEmpty, actions.count <= 8, hold.isFinite, (0...2).contains(hold) else {throw PlanError.invalid}
        var result:[UnitActionSegment]=[]
        for action in actions {
            guard let ticks=available[action], !ticks.isEmpty else {throw PlanError.missing(action)}
            guard ticks.count <= 64, ticks.allSatisfy({(1...600).contains($0)}) else {throw PlanError.invalid}
            result.append(UnitActionSegment(kind:action,ticks:ticks))
        }
        segments=result;self.hold=hold;self.repeats=repeats
    }
    enum PlanError: Error, Equatable {case invalid, missing(String)}
    var duration: Double {segments.reduce(0) {$0+$1.duration}+Double(segments.count-1)*hold}
    func sample(at elapsed: Double) -> UnitActionSample {
        let time=elapsed.isFinite ? max(0,elapsed) : 0
        if !repeats && time >= duration {
            let index=segments.count-1
            return UnitActionSample(segment:index,localTime:max(0,segments[index].duration-1e-9),completed:true,holding:true)
        }
        var remaining=repeats ? time.truncatingRemainder(dividingBy:duration) : time
        for (index,segment) in segments.enumerated() {
            if remaining+1e-9 < segment.duration {return UnitActionSample(segment:index,localTime:remaining,completed:false,holding:false)}
            remaining=max(0,remaining-segment.duration)
            if index < segments.count-1 && remaining+1e-9 < hold {
                return UnitActionSample(segment:index,localTime:max(0,segment.duration-1e-9),completed:false,holding:true)
            }
            if index < segments.count-1 {remaining=max(0,remaining-hold)}
        }
        return UnitActionSample(segment:0,localTime:0,completed:false,holding:false)
    }
}

// Source clips are original; routing/timebase remain a documented reconstruction.
// Chizuru's repeated attack is visible in the supplied recording. Other units
// use one complete attack (which may itself contain multiple swings), then idle.
struct ObtainedActionPolicy {
    var initialIdle = 0.8
    var attackCount = 1
    static func originalStyle(masterID: String) -> ObtainedActionPolicy {
        ObtainedActionPolicy(initialIdle: 0.8, attackCount: masterID == "100004604" ? 2 : 1)
    }
    func sample(at time: Double, attackTicks: [Int]?, idleTicks: [Int]) -> (kind: String, time: Double) {
        let elapsed = time.isFinite ? max(0,time) : 0
        guard let ticks=attackTicks, !ticks.isEmpty, ticks.allSatisfy({$0>0}),
              (1...3).contains(attackCount), initialIdle.isFinite, initialIdle>=0 else {return ("idle",elapsed)}
        let attack=Double(ticks.reduce(0,+))/60
        let idle=Double(idleTicks.reduce(0,+))/60
        var remaining=elapsed
        if remaining+1e-9 < initialIdle {return ("idle",remaining)}
        remaining = max(0,remaining-initialIdle)
        for index in 0..<attackCount {
            if remaining+1e-9 < attack {return ("atk",remaining)}
            remaining = max(0,remaining-attack)
            if index<attackCount-1 {
                if remaining+1e-9 < idle {return ("idle",remaining)}
                remaining = max(0,remaining-idle)
            }
        }
        return ("idle",remaining)
    }
}


// Presentation scale comes from the standing/idle body, never a beam or slash.
// The original unit-space anchor remains centered throughout every action.
enum ObtainedBodyFraming {
    static func scale(width: Double, height: Double, sourceWidth: Int, sourceHeight: Int) -> Double {
        guard width.isFinite, height.isFinite, width>0, height>0, sourceWidth>0, sourceHeight>0 else {return 1}
        return min(3.2,min(width*0.65/Double(sourceWidth),height*0.72/Double(sourceHeight)))
    }
}
