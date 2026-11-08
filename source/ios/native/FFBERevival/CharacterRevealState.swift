import Foundation

// Reconstructed timing, not recovered SpriteStudio keyframes. Active seconds only.
enum CharacterRevealPhase: String { case preparing, flash, materializing, obtained, waitingForContinue, finished }
enum CharacterRevealFinish: String { case completed, skipped, unavailable, failed, interrupted }
enum CharacterRevealTap { case ignored, advanced, completed }
enum CharacterRevealTiming {
    static let preparing = 0.06
    static let flash = 0.16
    static let materializing = 0.65
    static let obtained = 0.48
    static let maximumFrameDelta = 0.1
    static func duration(_ phase: CharacterRevealPhase) -> Double? {
        switch phase {
        case .preparing: return preparing
        case .flash: return flash
        case .materializing: return materializing
        case .obtained: return obtained
        default: return nil
        }
    }
}
struct CharacterRevealState {
    let receipt: CommittedSummon
    private(set) var index = 0
    private(set) var phase: CharacterRevealPhase = .preparing
    private(set) var elapsed = 0.0
    private(set) var motionTime = 0.0
    private(set) var suspended = false
    private(set) var reason: CharacterRevealFinish?
    var current: Award? { receipt.awards.indices.contains(index) ? receipt.awards[index] : nil }
    var progress: Double {
        guard let duration = CharacterRevealTiming.duration(phase) else { return 1 }
        return min(1,max(0,elapsed/duration))
    }
    mutating func suspend() { suspended = true }
    mutating func resume() { suspended = false }
    mutating func advance(_ delta: Double) {
        guard !suspended, reason == nil, delta.isFinite, delta >= 0 else { return }
        motionTime += delta; elapsed += delta
        while let duration = CharacterRevealTiming.duration(phase), elapsed >= duration {
            elapsed -= duration
            switch phase {
            case .preparing: phase = .flash
            case .flash: phase = .materializing
            case .materializing: phase = .obtained
            case .obtained: phase = .waitingForContinue
            default: return
            }
        }
    }
    // The event carries the displayed instance ID. Old/double taps cannot act on
    // another item; every next item also passes its own entrance before accepting taps.
    mutating func tap(expectedInstanceID: String) -> CharacterRevealTap {
        guard !suspended, reason == nil, phase == .waitingForContinue,
              current?.instance_id == expectedInstanceID else { return .ignored }
        if index+1 < receipt.awards.count {
            index += 1; phase = .preparing; elapsed = 0; return .advanced
        }
        _ = finish(.completed); return .completed
    }
    @discardableResult mutating func finish(_ why: CharacterRevealFinish) -> Bool {
        guard reason == nil else { return false }
        reason = why; phase = .finished; return true
    }
}

// Default-cell evidence in gacha_star1..6 supports these image families. Position,
// entrance and the explicit repeated count are reconstructed. Code 7/NV stays numeric.
enum CharacterRarityArtwork {
    static func star(_ rarity: Int?) -> String? {
        switch rarity {
        case 1,2: return "star_1"
        case 3: return "star_3"
        case 4: return "star_4"
        case 5,6: return "star_5"
        default: return nil
        }
    }
    static func count(_ rarity: Int?) -> Int? {
        guard let rarity, (1...6).contains(rarity) else { return nil }
        return rarity
    }
    static func flare(_ rarity: Int?) -> String? {
        switch rarity {
        case 3: return "stLight_3"
        case 4: return "stLight_4"
        case 5,6: return "stLight_5"
        default: return nil
        }
    }
}
