import Foundation

struct UnitAnimationClock {
    private(set) var elapsed = 0.0
    var paused = false
    var speed = 1.0
    mutating func advance(_ delta: Double) {
        guard !paused, delta.isFinite, delta >= 0, speed.isFinite, (0.25...2).contains(speed) else { return }
        elapsed += delta * speed
    }
    mutating func restart() { elapsed = 0 }
    static func frame(at seconds: Double, ticks: [Int], timebase: Double = 60) -> Int {
        guard seconds.isFinite, seconds >= 0, timebase > 0, !ticks.isEmpty, ticks.allSatisfy({ $0 > 0 }) else { return 0 }
        let total = Double(ticks.reduce(0,+))
        var position = (seconds * timebase).truncatingRemainder(dividingBy: total)
        for (index, duration) in ticks.enumerated() {
            if position < Double(duration) { return index }
            position -= Double(duration)
        }
        return 0
    }
}
