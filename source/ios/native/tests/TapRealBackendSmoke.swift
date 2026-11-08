import Foundation

@main struct TapRealBackendSmoke {
    @MainActor static func main() async throws {
        let backend = try HTTPBackend(address: CommandLine.arguments[1]); let model = SummonModel()
        await model.refresh(using: backend,identity: "isolated")
        let banner = model.banners.first { $0.id == "9100203" }!
        let single = banner.offer_details.first!; let multi = banner.offer_details.last!
        async let first = model.summon(banner,offer: single,using: backend,identity: "isolated")
        async let duplicate = model.summon(banner,offer: single,using: backend,identity: "isolated")
        let pair = await [first,duplicate]
        precondition(pair.filter { $0 }.count == 1 && model.results.count == 1)
        precondition(model.campaign?.currencies["lapis_free"] == 9500)
        guard let receipt = model.committedSummon else { fatalError("Missing single receipt") }
        var gate = SummonRevealGate(receipt: receipt)
        precondition(gate.finish()?.map(\.instance_id) == model.results.map(\.instance_id) && gate.finish() == nil)
        let many = await model.summon(banner,offer: multi,using: backend,identity: "isolated")
        precondition(many && model.results.count == 11 && model.campaign?.currencies["lapis_free"] == 4500)
        let beforeLoss = model.results.map(\.instance_id)
        let lost = await model.summon(banner,offer: single,using: backend,identity: "isolated")
        precondition(!lost && model.needsRefresh && model.committedSummon == nil)
        precondition(model.results.map(\.instance_id) == beforeLoss)
        let noRetry = await model.summon(banner,offer: single,using: backend,identity: "isolated")
        precondition(!noRetry)
        await model.refresh(using: backend,identity: "isolated")
        precondition(model.results.count == 1 && model.campaign?.currencies["lapis_free"] == 4000)
        let savedIDs = model.results.map(\.instance_id)
        let reloaded = SummonModel(); await reloaded.refresh(using: backend,identity: "isolated")
        precondition(reloaded.results.map(\.instance_id) == savedIDs && reloaded.campaign?.currencies["lapis_free"] == 4000)
        print("Real Python/Swift contract passed: exactly one single + one 11-pull, duplicate guard, post-commit error, no reroll, exact saved-state reconciliation")
    }
}
