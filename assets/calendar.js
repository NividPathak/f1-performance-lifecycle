// from formula1.com/en/racing/2026
const CALENDAR_2026 = [
  { round: 1, gp: "Australian Grand Prix", circuit: "Albert Park Circuit, Melbourne", country: "Australia" },
  { round: 2, gp: "Chinese Grand Prix", circuit: "Shanghai International Circuit", country: "China" },
  { round: 3, gp: "Japanese Grand Prix", circuit: "Suzuka Circuit", country: "Japan" },
  { round: 4, gp: "Miami Grand Prix", circuit: "Miami International Autodrome", country: "United States" },
  { round: 5, gp: "Canadian Grand Prix", circuit: "Circuit Gilles Villeneuve, Montreal", country: "Canada" },
  { round: 6, gp: "Monaco Grand Prix", circuit: "Circuit de Monaco", country: "Monaco" },
  { round: 7, gp: "Barcelona-Catalunya Grand Prix", circuit: "Circuit de Barcelona-Catalunya", country: "Spain" },
  { round: 8, gp: "Austrian Grand Prix", circuit: "Red Bull Ring, Spielberg", country: "Austria" },
  { round: 9, gp: "British Grand Prix", circuit: "Silverstone Circuit", country: "United Kingdom" },
  { round: 10, gp: "Belgian Grand Prix", circuit: "Circuit de Spa-Francorchamps", country: "Belgium" },
  { round: 11, gp: "Hungarian Grand Prix", circuit: "Hungaroring, Mogyorod", country: "Hungary" },
  { round: 12, gp: "Dutch Grand Prix", circuit: "Circuit Zandvoort", country: "Netherlands" },
  { round: 13, gp: "Italian Grand Prix", circuit: "Monza Circuit", country: "Italy" },
  { round: 14, gp: "Spanish Grand Prix", circuit: "Madring, Madrid", country: "Spain" },
  { round: 15, gp: "Azerbaijan Grand Prix", circuit: "Baku City Circuit", country: "Azerbaijan" },
  { round: 16, gp: "Bahrain Grand Prix", circuit: "Sepang International Circuit", country: "Malaysia" },
  { round: 17, gp: "Singapore Grand Prix", circuit: "Marina Bay Street Circuit", country: "Singapore" },
  { round: 18, gp: "United States Grand Prix", circuit: "Circuit of the Americas, Austin", country: "United States" },
  { round: 19, gp: "Mexico City Grand Prix", circuit: "Autodromo Hermanos Rodriguez", country: "Mexico" },
  { round: 20, gp: "Sao Paulo Grand Prix", circuit: "Interlagos Circuit", country: "Brazil" },
  { round: 21, gp: "Las Vegas Grand Prix", circuit: "Las Vegas Strip Circuit", country: "United States" },
  { round: 22, gp: "Qatar Grand Prix", circuit: "Lusail International Circuit", country: "Qatar" },
  { round: 23, gp: "Abu Dhabi Grand Prix", circuit: "Yas Marina Circuit", country: "United Arab Emirates" },
];

document.addEventListener("DOMContentLoaded", () => {
  const body = document.getElementById("calendar-body");
  if (!body) return;
  body.innerHTML = CALENDAR_2026.map(
    (r) => `<tr><td>${r.round}</td><td>${r.gp}</td><td>${r.circuit}</td><td>${r.country}</td></tr>`
  ).join("");
});
