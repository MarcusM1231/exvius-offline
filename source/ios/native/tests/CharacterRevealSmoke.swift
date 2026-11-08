import Foundation
@main struct CharacterRevealSmoke {
    static func main() throws {
        for count in [1,11] {
            let awards = (0..<count).map { Award(instance_id: String($0),unit_id: $0 == 0 ? "202000203" : "100004203",name: "Frozen fixture",granted_rarity: $0%6+1) }
            let receipt = CommittedSummon(id: UUID(),bannerID: "b",offerID: "o",backendIdentity: "test",awards: awards)
            var sequence = CharacterRevealState(receipt: receipt)
            precondition(sequence.tap(expectedInstanceID: "0") == .ignored)
            for index in 0..<count {
                precondition(sequence.index == index && sequence.current?.unit_id == awards[index].unit_id)
                sequence.advance(CharacterRevealTiming.preparing/2)
                let phase = sequence.phase, elapsed = sequence.elapsed
                sequence.suspend();sequence.advance(999);precondition(sequence.phase == phase && sequence.elapsed == elapsed)
                precondition(sequence.tap(expectedInstanceID: awards[index].instance_id) == .ignored);sequence.resume()
                sequence.advance(2);precondition(sequence.phase == .waitingForContinue)
                for _ in 0..<1000 {sequence.advance(1000)}
                precondition(sequence.phase == .waitingForContinue && sequence.index == index)
                sequence.suspend();sequence.advance(999);precondition(sequence.tap(expectedInstanceID: awards[index].instance_id) == .ignored);sequence.resume()
                precondition(sequence.tap(expectedInstanceID: "wrong-token") == .ignored)
                let result = sequence.tap(expectedInstanceID: awards[index].instance_id)
                precondition(result == (index+1 == count ? .completed : .advanced))
                for _ in 0..<50 {precondition(sequence.tap(expectedInstanceID: awards[index].instance_id) == .ignored)}
            }
            precondition(sequence.phase == .finished && sequence.reason == .completed)
            precondition(!sequence.finish(.skipped) && CommittedSummon.sameAwards(sequence.receipt.awards,awards))
            for reason in [CharacterRevealFinish.skipped,.failed,.interrupted,.unavailable] {
                var cancelled = CharacterRevealState(receipt: receipt);precondition(cancelled.finish(reason))
                precondition(!cancelled.finish(.completed));cancelled.advance(99)
                precondition(cancelled.reason == reason && CommittedSummon.sameAwards(cancelled.receipt.awards,awards))
            }
        }
        for (code,image) in [(1,"star_1"),(2,"star_1"),(3,"star_3"),(4,"star_4"),(5,"star_5"),(6,"star_5")] {
            precondition(CharacterRarityArtwork.star(code) == image && CharacterRarityArtwork.count(code) == code)
        }
        for code in [nil,0,7,8,999] as [Int?] {precondition(CharacterRarityArtwork.star(code) == nil && CharacterRarityArtwork.count(code) == nil)}
        let receipt = CommittedSummon(id: UUID(),bannerID: "b",offerID: "o",backendIdentity: "test",awards: [Award(instance_id: "a",unit_id: "m",name: nil,granted_rarity: nil)])
        var sequence = CharacterRevealState(receipt: receipt);sequence.advance(.nan);sequence.advance(.infinity);sequence.advance(-1)
        precondition(sequence.phase == .preparing && sequence.elapsed == 0)
        sequence.advance(0.07);precondition(sequence.phase == .flash)
        sequence.advance(0.17);precondition(sequence.phase == .materializing)
        sequence.advance(0.65);precondition(sequence.phase == .obtained)
        sequence.advance(0.5);precondition(sequence.phase == .waitingForContinue)
        print("Character reveal state, 1/11 cursor, exactly-once, pause, rarity, immutable-award contracts passed")
    }
}
