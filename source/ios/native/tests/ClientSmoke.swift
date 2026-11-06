// Compile with API.swift to verify the real URLSession/JSON contract on macOS.
import Foundation

@main
struct ClientSmoke {
    @MainActor static func main() async throws {
        guard CommandLine.arguments.count == 2 else { fatalError("Pass an isolated demo API URL") }
        // Cover legacy duplicate awards deterministically, independent of RNG.
        for (raw, expected) in [("4", Optional(4)), ("\"4\"", Optional(4)), ("null", nil)] {
            let json = "{\"instance_id\":\"1\",\"unit_id\":\"100\",\"granted_rarity\":\(raw)}"
            let award = try JSONDecoder().decode(Award.self, from: Data(json.utf8))
            precondition(award.granted_rarity == expected)
        }
        let api = try API(address: CommandLine.arguments[1])
        let banners: BannersResponse = try await api.request("v1/banners")
        guard let banner = banners.banners.first(where: { $0.id == "9100203" }) else {
            fatalError("Expected authored demo banner")
        }
        precondition(banner.offer_details.map(\.draws) == [1, 11])
        let before: Campaign = try await api.request("v1/state")
        let response: SummonResponse = try await api.request("v1/summons",
            body: ["banner_id": banner.id, "offer": "primary"])
        precondition(response.state.units.count == before.units.count + 1)
        precondition(response.state.currencies["lapis_free"] == (before.currencies["lapis_free"] ?? 0) - 500)
        precondition(response.result.awards.count == 1)
        let model = SummonModel()
        await model.refresh(CommandLine.arguments[1])
        precondition(model.error == nil && model.results.count == 1)
        precondition(model.campaign?.units.count == response.state.units.count)
        print("Swift URLSession contract passed: banners, summon, currency, collection, saved results")
    }
}
