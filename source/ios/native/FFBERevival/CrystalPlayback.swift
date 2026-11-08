import Foundation

// Authored reconstruction, in seconds. No BMB frame count or original timing claim.
enum CrystalAppearance: String, CaseIterable, Identifiable {
    case blue = "Blue", gold = "Gold", rainbow = "Rainbow"
    var id: String { rawValue }
}
enum CrystalPlaybackState: String { case inspection, playing, paused, stopped, finished }
enum CrystalPlaybackOutcome { case finished, cancelled, unavailable }
struct CrystalPose {
    let stage: String
    let scale: Double
    let opacity: Double
    let lift: Double
    let turn: Double
    let opening: Double
    let flash: Double
    static func sample(_ seconds: Double) -> CrystalPose {
        let t = max(0, min(CrystalClock.duration, seconds.isFinite ? seconds : 0))
        func smooth(_ x: Double) -> Double { let u = max(0,min(1,x)); return u*u*(3-2*u) }
        let arrival = smooth(t/0.9)
        let opening = smooth((t-2.55)/1.05)
        let flash = max(0,1-abs(t-2.65)/0.32)
        return CrystalPose(stage: t < 0.9 ? "Arrival" : t < 2.55 ? "Idle" : t < 3.75 ? "Opening" : "Reveal ready",
            scale: 0.28+0.72*arrival, opacity: arrival*(1-smooth((t-3.05)/0.7)),
            lift: (1-arrival)*8 + sin(t*2.4)*0.25, turn: sin(t*0.9)*0.12,
            opening: opening, flash: flash)
    }
}
struct CrystalClock {
    static let duration = 4.15
    private(set) var time = 1.6
    private(set) var state: CrystalPlaybackState = .inspection
    var speed = 1.0
    mutating func play() {
        if state != .paused { time = 0 }
        state = .playing
    }
    mutating func pause() { if state == .playing { state = .paused } }
    mutating func restart() { time = 0; state = .playing }
    mutating func stop() { time = 0; state = .stopped }
    mutating func inspect() { time = 1.6; state = .inspection }
    mutating func seek(_ value: Double) { time = max(0,min(Self.duration,value.isFinite ? value : 0)); state = .paused }
    @discardableResult mutating func advance(_ delta: Double) -> Bool {
        guard state == .playing, delta.isFinite, delta >= 0 else { return false }
        let safeSpeed = speed.isFinite ? max(0.25,min(2,speed)) : 1
        time = min(Self.duration,time+delta*safeSpeed)
        if time >= Self.duration { state = .finished; return true }
        return false
    }
}
