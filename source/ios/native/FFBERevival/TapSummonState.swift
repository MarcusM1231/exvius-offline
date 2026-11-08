import Foundation

// Shared production/Developer tap gate. The legacy automatic demo clock remains separate.
enum TapSummonPhase: String { case fallingCrystals, arriving, waitingForTap, opening, revealing, finished }
struct TapSummonClock {
    private(set) var phase: TapSummonPhase
    let includesFalling: Bool
    init(includeFalling: Bool = true) { includesFalling = includeFalling; phase = includeFalling ? .fallingCrystals : .arriving }
    private(set) var elapsed = 0.0
    private(set) var suspended = false
    private(set) var motionTime = 0.0
    var showsTouchPrompt: Bool { phase == .waitingForTap }
    var sourceTime: Double {
        switch phase {
        case .fallingCrystals: return 0
        case .arriving: return min(0.9,elapsed)
        case .waitingForTap: return 0.9 // Hold opening progression; motion has its own continuous clock.
        case .opening: return 2.55+min(1.2,elapsed)
        case .revealing: return 3.75+min(0.4,elapsed)
        case .finished: return CrystalClock.duration
        }
    }
    mutating func suspend() { suspended = true }
    mutating func resume() { suspended = false }
    // Taps during arrival are ignored, never buffered; repeats cannot restart opening.
    @discardableResult mutating func tap() -> Bool {
        guard !suspended, phase == .waitingForTap else { return false }
        phase = .opening; elapsed = 0; return true
    }
    @discardableResult mutating func advance(_ delta: Double) -> Bool {
        guard !suspended, delta.isFinite, delta >= 0, phase != .finished else { return false }
        motionTime += delta
        switch phase {
        case .fallingCrystals:
            elapsed += delta
            if elapsed+1e-9 >= CrystalEntranceTiming.fallingDuration {
                elapsed -= CrystalEntranceTiming.fallingDuration; phase = .arriving
                if elapsed+1e-9 >= CrystalEntranceTiming.arrivalDuration { phase = .waitingForTap; elapsed = 0 }
            }
        case .arriving:
            elapsed += delta
            if elapsed+1e-9 >= CrystalEntranceTiming.arrivalDuration { phase = .waitingForTap; elapsed = 0 }
        case .waitingForTap:
            // Bounded loop time. There is deliberately NO transition out without tap.
            elapsed = (elapsed+delta.truncatingRemainder(dividingBy: 1.35)).truncatingRemainder(dividingBy: 1.35)
        case .opening:
            elapsed += delta
            if elapsed >= 1.2 { phase = .revealing; elapsed = 0 }
        case .revealing:
            elapsed += delta
            if elapsed >= 0.4 { phase = .finished; elapsed = 0; return true }
        case .finished: break
        }
        return false
    }
}

enum SummonRevealReason { case opened, skipped, unavailable, interrupted }
struct SummonRevealGate {
    let receipt: CommittedSummon
    private(set) var completed = false
    private(set) var reason: SummonRevealReason?
    // Shared by opening completion, Skip, unavailable content and dismissal.
    mutating func finish(reason: SummonRevealReason = .opened) -> [Award]? {
        guard !completed else { return nil }
        completed = true; self.reason = reason; return receipt.awards
    }
}
extension CommittedSummon {
    var crystalAppearance: CrystalAppearance {
        // Reconstruction mapping only: 1–3 blue, 4 gold, 5–8 rainbow (including NV).
        // Unknown or malformed rarity never changes the award; fallback is blue.
        let valid = awards.compactMap(\.granted_rarity).filter { (1...8).contains($0) }
        guard let highest = valid.max() else { return .blue }
        return highest >= 5 ? .rainbow : highest == 4 ? .gold : .blue
    }
}
