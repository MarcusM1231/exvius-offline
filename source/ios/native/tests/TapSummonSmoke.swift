import Foundation

@MainActor final class CountingSummonBackend: SummonBackend {
    enum Fault { case none, refusal, lostAfterCommit, mismatchedResponse }
    var calls = 0
    var fault: Fault = .none
    var stored = Campaign(demo_metadata: true,currencies: ["lapis_free":10000],units: [],last_pull: nil)
    let banner = Banner(id: "test",name: "Isolated fixture",supported: true,offer_details: [
        Offer(offer: "primary",cost: Cost(kind: "lapis",amount: 500),draws: 1),
        Offer(offer: "secondary",cost: Cost(kind: "lapis",amount: 5000),draws: 11)])
    func banners() async throws -> BannersResponse { BannersResponse(banners: [banner]) }
    func state() async throws -> Campaign { stored }
    func summon(bannerID: String, offer: String) async throws -> SummonResponse {
        calls += 1
        try await Task.sleep(nanoseconds: 10_000_000)
        let count = offer == "primary" ? 1 : 11; let cost = count == 1 ? 500 : 5000
        guard fault != .refusal, (stored.currencies["lapis_free"] ?? 0)>=cost else { throw APIError(message: "Insufficient Lapis") }
        var awards: [Award] = []
        let firstID = stored.units.count+1
        for index in 0..<count {
            let rarity: Int = index == 0 ? 4 : 3
            awards.append(Award(instance_id: String(firstID+index),unit_id: "100004203",name: "Fixture",granted_rarity: rarity))
        }
        let saved = Pull(awards: awards,banner_id: bannerID,count: count)
        stored = Campaign(demo_metadata: true,currencies: ["lapis_free":stored.currencies["lapis_free"]!-cost],
            units: stored.units+awards.map { UnitRecord(instance_id: $0.instance_id,master_id: $0.unit_id,name: $0.name,level: 1,granted_rarity: $0.granted_rarity) },last_pull: saved)
        if fault == .lostAfterCommit { throw APIError(message: "Response lost after commit") }
        let response = fault == .mismatchedResponse ? Pull(awards: awards,banner_id: "wrong",count: count) : saved
        return SummonResponse(result: response,state: stored)
    }
}

@main struct TapSummonSmoke {
    @MainActor static func main() async throws {
        var clock = TapSummonClock()
        precondition(!clock.tap()) // arrival taps ignored
        clock.advance(CrystalEntranceTiming.totalArrival); precondition(clock.phase == .waitingForTap)
        for _ in 0..<10000 { precondition(!clock.advance(1000)); precondition(clock.phase == .waitingForTap && clock.sourceTime < 2.55) }
        var continuous = TapSummonClock(); continuous.advance(CrystalEntranceTiming.totalArrival)
        let startMotion = continuous.motionTime
        for _ in 0..<135 { continuous.advance(0.01) }
        precondition(abs(continuous.motionTime-(startMotion+1.35))<1e-8 && continuous.sourceTime == 0.9)
        let beforeTapMotion = continuous.motionTime
        precondition(continuous.tap() && continuous.motionTime == beforeTapMotion)
        clock.suspend(); precondition(!clock.tap()); let held = clock.sourceTime
        let heldMotion = clock.motionTime
        clock.advance(1000); precondition(clock.sourceTime == held && clock.motionTime == heldMotion); clock.resume()
        precondition(clock.phase == .waitingForTap && clock.tap())
        for _ in 0..<20 { precondition(!clock.tap()) }
        clock.advance(0.6); clock.suspend(); clock.advance(100); precondition(clock.phase == .opening)
        clock.resume(); clock.advance(0.6); precondition(clock.phase == .revealing)
        precondition(clock.advance(0.4) && clock.phase == .finished)
        precondition(!clock.advance(100) && !clock.tap())
        let backend = CountingSummonBackend(); let model = SummonModel()
        await model.refresh(using: backend,identity: "test")
        async let one = model.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        async let duplicate = model.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        let accepted = await [one,duplicate]
        precondition(accepted.filter { $0 }.count == 1 && backend.calls == 1)
        guard let first = model.committedSummon else { fatalError("No committed receipt") }
        var gate = SummonRevealGate(receipt: first)
        precondition(!gate.completed && first.crystalAppearance == .gold)
        precondition(gate.finish()?.map(\.instance_id) == first.awards.map(\.instance_id))
        precondition(gate.finish() == nil)
        for reason in [SummonRevealReason.skipped,.unavailable,.interrupted,.opened] {
            var fallback = SummonRevealGate(receipt: first)
            precondition(fallback.finish(reason: reason)?.map(\.instance_id) == first.awards.map(\.instance_id))
            precondition(fallback.reason == reason && fallback.finish(reason: .opened) == nil)
        }
        let multi = await model.summon(backend.banner,offer: backend.banner.offer_details[1],using: backend,identity: "test")
        precondition(multi && backend.calls == 2 && model.results.count == 11 && model.campaign?.currencies["lapis_free"] == 4500)
        precondition(model.committedSummon?.crystalAppearance == .gold)
        // Later state/refresh must not replace an earlier frozen presentation.
        var frozen = SummonRevealGate(receipt: first)
        precondition(frozen.finish()?.map(\.instance_id) == first.awards.map(\.instance_id))
        precondition(first.awards.count == 1 && model.results.count == 11)
        let saved = model.results
        backend.fault = .refusal
        let refused = await model.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        precondition(!refused && model.committedSummon == nil && CommittedSummon.sameAwards(model.results,saved))
        let refusedAgain = await model.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        precondition(!refusedAgain && backend.calls == 3) // refresh required, never retry
        await model.refresh(using: backend,identity: "test")
        backend.fault = .lostAfterCommit
        let lost = await model.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        precondition(!lost && model.needsRefresh && model.committedSummon == nil && backend.calls == 4)
        let cold = SummonModel(); await cold.refresh(using: backend,identity: "test")
        precondition(cold.results.count == 1 && cold.results[0].instance_id == backend.stored.last_pull!.awards[0].instance_id)
        precondition(cold.campaign?.currencies["lapis_free"] == 4000 && backend.calls == 4)
        backend.fault = .mismatchedResponse
        let mismatch = await cold.summon(backend.banner,offer: backend.banner.offer_details[0],using: backend,identity: "test")
        precondition(!mismatch && cold.committedSummon == nil && cold.needsRefresh)
        for (json,expected) in [("3",CrystalAppearance.blue),("4",.gold),("5",.rainbow),("8",.rainbow),("999",.blue),("\"bad\"",.blue),("true",.blue),("null",.blue)] {
            let award = try JSONDecoder().decode(Award.self,from: Data("{\"instance_id\":\"1\",\"unit_id\":\"100\",\"granted_rarity\":\(json)}".utf8))
            let receipt = CommittedSummon(id: UUID(),bannerID: "b",offerID: "o",backendIdentity: "test",awards: [award])
            precondition(receipt.crystalAppearance == expected)
        }
        print("Tap summon contract passed: indefinite wait, arrival tap ignored, single opening, lifecycle pause, one completion, Skip idempotence, one transaction per single/multi, duplicate guard, refusal, ambiguous reconciliation, cold reload, mismatch rejection and rarity fallback")
    }
}
