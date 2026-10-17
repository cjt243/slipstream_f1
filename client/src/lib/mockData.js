// Mock data matching the API contract shapes (docs/api-contracts.md).
// Hooks fall back to these until the backend endpoints exist.

export const MOCK_CONSTRUCTORS = [
  { id: 1, name: "McLaren", color: "#FF8000", salary: 30_000_000, season: 2025 },
  { id: 2, name: "Ferrari", color: "#E80020", salary: 27_400_000, season: 2025 },
  { id: 3, name: "Mercedes", color: "#27F4D2", salary: 24_800_000, season: 2025 },
  { id: 4, name: "Red Bull Racing", color: "#3671C6", salary: 22_200_000, season: 2025 },
  { id: 5, name: "Williams", color: "#64C4FF", salary: 19_600_000, season: 2025 },
];

export const MOCK_DRIVERS = [
  { id: 1, name: "Lando Norris", driver_number: 4, constructor_id: 1, constructor_name: "McLaren", constructor_color: "#FF8000", salary: 32_400_000, season: 2025 },
  { id: 2, name: "Oscar Piastri", driver_number: 81, constructor_id: 1, constructor_name: "McLaren", constructor_color: "#FF8000", salary: 30_800_000, season: 2025 },
  { id: 3, name: "Charles Leclerc", driver_number: 16, constructor_id: 2, constructor_name: "Ferrari", constructor_color: "#E80020", salary: 29_200_000, season: 2025 },
  { id: 4, name: "Lewis Hamilton", driver_number: 44, constructor_id: 2, constructor_name: "Ferrari", constructor_color: "#E80020", salary: 26_000_000, season: 2025 },
  { id: 5, name: "George Russell", driver_number: 63, constructor_id: 3, constructor_name: "Mercedes", constructor_color: "#27F4D2", salary: 27_600_000, season: 2025 },
  { id: 6, name: "Max Verstappen", driver_number: 1, constructor_id: 4, constructor_name: "Red Bull Racing", constructor_color: "#3671C6", salary: 34_000_000, season: 2025 },
  { id: 7, name: "Alexander Albon", driver_number: 23, constructor_id: 5, constructor_name: "Williams", constructor_color: "#64C4FF", salary: 22_800_000, season: 2025 },
  { id: 8, name: "Kimi Antonelli", driver_number: 12, constructor_id: 3, constructor_name: "Mercedes", constructor_color: "#27F4D2", salary: 24_400_000, season: 2025 },
];
