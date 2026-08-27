// Real Sri Lanka photography shipped with the app, mapped to the attractions
// it depicts. One place to answer "which photo shows this attraction?" so
// cards, heroes, and suggestion tiles all agree.
//
// Each entry is { src, position, alt }: `position` is the CSS object-position
// that keeps the photo's subject visible when a portrait shot is cropped into
// a wide card or hero.

import sigiriyaAerialSrc from './sigiriya.jpg'
import sigiriyaGroundSrc from './SIGIRIYA.jpeg'
import templeOfToothSrc from './temple of tooth sri lanka.jpeg'
import galleFortSrc from './galle_fort.jpg'
import galleFortAltSrc from './galle_fort_2.jpg'
import galleLighthouseSrc from './galle_lighthouse.jpg'
import nineArchSrc from './9n arch.jpg'
import leopardSrc from './lepordjpg.jpg'
import elephantSrc from './elephant.jpg'
import adamsPeakSrc from "./Adam's_peak.jpeg"
import dambullaSrc from './Dambulla.jpeg'
import stClairsFallsSrc from "./St_ Clair's Falls in Hatton, Sri Lanka.jpeg"
import coconutTreeHillSrc from './Coconut Tree Hill, Mirissa.jpeg'
import whaleWatchingSrc from './Whale Watching Mirissa, Sri Lanka.jpeg'
import stiltFishingSrc from './Sri Lanka Travel – Stilt Fishing at Sunset on the Coast.jpeg'
import hikkaduwaBeachSrc from './Hikkaduwa_beach.jpg'
import hikkaduwaCoralSrc from './Hikkaduwa_coral.jpg'
import hikkaduwaDivingSrc from './Hikkaduwa_diving.jpg'
import blueBeachIslandSrc from './𝐁𝐥𝐮𝐞 𝐁𝐞𝐚𝐜𝐡 𝐈𝐬𝐥𝐚𝐧𝐝, 𝐍𝐢𝐥𝐰𝐞𝐥𝐥i.jpeg'
import knucklesRangeSrc from './Knuckles Mountain Range.jpeg'
import ellaRockSrc from './Ella Rock - Ella, SriLanka.jpeg'
import harithaKandaSrc from './Haritha kanda or Green Mountain - Bopaththalawa, SriLanka.jpeg'
import hortonPlainsSrc from './horton_pains.webp'
import wilpattuSrc from './Wilpaththu National Park.jpeg'
import polonnaruwaSrc from './Polonnaruwa, Sri Lanka.jpeg'
import anuradhapuraSrc from './Anuradhapura.jpeg'
import bahirawakandaSrc from './Bahirawakanda_Vihara_Budda_Statue.jpg'
import bambarakandaSrc from './Bambarakanda_falls.jpg'
import ceylonTeaMuseumSrc from './Ceylon_Tea_Museum.jpg'
import colomboLotusTowerSrc from './Colombo_Lotus_Tower.jpg'
import delftIslandSrc from './Delft_Island.jpg'
import diyalumaFallsSrc from './Diyaluma_Falls.jpg'
import gangaramayaTempleSrc from './Gangaramaya_Temple.jpg'
import gregoryLakeSrc from './Gregory_Lake.jpg'
import hakgalaBotanicalGardenSrc from './Hakgala_Botanical_Garden.jpg'
import isurumuniyaSrc from './Isurumuniya.jpg'
import jaffnaFortSrc from './Jaffna_Fort.jpg'
import jaffnaPublicLibrarySrc from './Jaffna_Public_Library.jpg'
import japanesePeacePagodaSrc from './Japanese_Peace_Pagoda.jpg'
import jetavanaramayaSrc from './Jetavanaramaya.jpg'
import kalpitiyaPeninsulaSrc from './Kalpitiya_Peninsula.jpg'
import kandyViewPointSrc from './Kandy_View_Point.jpg'
import keerimalaiSpringSrc from './Keerimalai_Spring.jpg'
import kelaniyaRajaMahaViharaSrc from './Kelaniya_Raja_Maha_Vihara.jpg'
import kithalEllaWaterfallSrc from './Kithal_Ella_Waterfall.jpg'
import kithulgalaSrc from './Kithulgala.jpg'
import abayagiriViharayaSrc from './abayagiri_viharaya.jpg'
import ambuluwawaTowerSrc from './ambuluwawa_tower.jpg'
import koneswaramTempleSrc from './koneswaram_temple.jpg'
import kosgodaSeaTurtleConservationProjectSrc from './kosgoda_sea_turtle_conservation_project.jpg'
import liptonSeatSrc from './lipton_seat.jpg'
import littleAdamsPeakSrc from './little_adams_peak.jpg'
import loversLeapWaterfallSrc from './lovers_leap_waterfall.jpg'
import madihaBeachSrc from './madiha_beach.jpg'
import mihintaleSrc from './mihintale.webp'
import moonPlainsSrc from './moon_plains.jpg'
import muthurajawelaMarshSrc from './muthurajawela_marsh.jpg'
import nagadepaPuranaViharaSrc from './nagadepa_purana_vihara.jpg'
import nallurKandaswamyTempleSrc from './nallur_kandaswamy_temple.jpg'
import nationalMaritimeMuseumSrc from './national_maritime_museum.jpg'
import parrotRockBridgeSrc from './parrot_rock_bridge.jpg'
import pedroTeaEstateSrc from './pedro_tea_Estate.jpg'
import pidurangalaSrc from './pidurangala.jpg'
import pointPedroSrc from './point_pedro.jpg'
import yapahuwaRockFortressSrc from './yapahuwa_rock_fortress.jpg'

/** Named, hand-cropped scenes for editorial use (heroes, feature tiles). */
export const scenes = {
  sigiriyaAerial: {
    src: sigiriyaAerialSrc,
    position: '50% 45%',
    alt: 'Sigiriya Rock Fortress rising over the jungle at golden hour',
  },
  sigiriyaGround: {
    src: sigiriyaGroundSrc,
    position: '50% 38%',
    alt: 'Sigiriya Rock Fortress seen from its water gardens',
  },
  templeOfTooth: {
    src: templeOfToothSrc,
    position: '50% 45%',
    alt: 'A tusker elephant before the Temple of the Sacred Tooth Relic, Kandy',
  },
  galleFort: {
    src: galleFortSrc,
    position: '50% 62%',
    alt: 'The clock tower and ramparts of Galle Fort',
  },
  galleFortAlt: {
    src: galleFortAltSrc,
    position: '50% 50%',
    alt: 'Inside the old town of Galle Fort',
  },
  galleLighthouse: {
    src: galleLighthouseSrc,
    position: '50% 45%',
    alt: 'Galle lighthouse among coconut palms at sunset',
  },
  nineArch: {
    src: nineArchSrc,
    position: '50% 45%',
    alt: 'A blue train crossing the Nine Arch Bridge in Ella',
  },
  leopard: {
    src: leopardSrc,
    position: '50% 35%',
    alt: 'A Sri Lankan leopard resting on a branch in Yala',
  },
  elephant: {
    src: elephantSrc,
    position: '50% 55%',
    alt: 'A tusker elephant by the water',
  },
  adamsPeak: {
    src: adamsPeakSrc,
    position: '50% 40%',
    alt: "The stairway descending Adam's Peak above the clouds",
  },
  dambulla: {
    src: dambullaSrc,
    position: '50% 45%',
    alt: 'The white gateway of the Dambulla cave temples beneath the rock overhang',
  },
  stClairsFalls: {
    src: stClairsFallsSrc,
    position: '50% 50%',
    alt: "St. Clair's Falls cascading through tea country",
  },
  coconutTreeHill: {
    src: coconutTreeHillSrc,
    /* Cropped low: the source photo has a location caption near the top edge. */
    position: '50% 68%',
    alt: 'Palm trees over the ocean at Coconut Tree Hill, Mirissa',
  },
  whaleWatching: {
    src: whaleWatchingSrc,
    position: '50% 40%',
    alt: 'A blue whale breaching off Mirissa',
  },
  stiltFishing: {
    src: stiltFishingSrc,
    position: '50% 55%',
    alt: 'Stilt fishermen silhouetted against a sunset on the southern coast',
  },
  hikkaduwaBeach: {
    src: hikkaduwaBeachSrc,
    position: '50% 50%',
    alt: 'Hikkaduwa beach',
  },
  hikkaduwaCoral: {
    src: hikkaduwaCoralSrc,
    position: '50% 50%',
    alt: 'Corals in the shallows at Hikkaduwa',
  },
  hikkaduwaDiving: {
    src: hikkaduwaDivingSrc,
    position: '50% 50%',
    alt: 'Diving over a reef at Hikkaduwa',
  },
  blueBeachIsland: {
    src: blueBeachIslandSrc,
    position: '50% 50%',
    alt: 'Blue Beach Island at Nilwella',
  },
  knucklesRange: {
    src: knucklesRangeSrc,
    position: '50% 45%',
    alt: 'The jagged peaks of the Knuckles Mountain Range',
  },
  ellaRock: {
    src: ellaRockSrc,
    position: '50% 45%',
    alt: 'The view from the summit of Ella Rock',
  },
  harithaKanda: {
    src: harithaKandaSrc,
    position: '50% 45%',
    alt: 'Haritha Kanda (Green Mountain) above Bopaththalawa',
  },
  hortonPlains: {
    src: hortonPlainsSrc,
    position: '50% 50%',
    alt: "Misty grassland at Horton Plains, near World's End",
  },
  wilpattu: {
    src: wilpattuSrc,
    position: '50% 50%',
    alt: 'A watering hole in Wilpattu National Park',
  },
  polonnaruwa: {
    src: polonnaruwaSrc,
    position: '50% 50%',
    alt: 'Ancient ruins of the medieval capital, Polonnaruwa',
  },
  anuradhapura: {
    src: anuradhapuraSrc,
    position: '50% 50%',
    alt: 'The sacred dagobas of Anuradhapura',
  },
  bahirawakanda: { src: bahirawakandaSrc, position: '50% 50%', alt: 'Bahirawakanda Vihara Buddha Statue' },
  bambarakanda: { src: bambarakandaSrc, position: '50% 50%', alt: 'Bambarakanda Falls' },
  ceylonTeaMuseum: { src: ceylonTeaMuseumSrc, position: '50% 50%', alt: 'Ceylon Tea Museum' },
  colomboLotusTower: { src: colomboLotusTowerSrc, position: '50% 50%', alt: 'Colombo Lotus Tower' },
  delftIsland: { src: delftIslandSrc, position: '50% 50%', alt: 'Delft Island' },
  diyalumaFalls: { src: diyalumaFallsSrc, position: '50% 50%', alt: 'Diyaluma Falls' },
  gangaramayaTemple: { src: gangaramayaTempleSrc, position: '50% 50%', alt: 'Gangaramaya Temple' },
  gregoryLake: { src: gregoryLakeSrc, position: '50% 50%', alt: 'Gregory Lake' },
  hakgalaBotanicalGarden: { src: hakgalaBotanicalGardenSrc, position: '50% 50%', alt: 'Hakgala Botanical Garden' },
  isurumuniya: { src: isurumuniyaSrc, position: '50% 50%', alt: 'Isurumuniya' },
  jaffnaFort: { src: jaffnaFortSrc, position: '50% 50%', alt: 'Jaffna Fort' },
  jaffnaPublicLibrary: { src: jaffnaPublicLibrarySrc, position: '50% 50%', alt: 'Jaffna Public Library' },
  japanesePeacePagoda: { src: japanesePeacePagodaSrc, position: '50% 50%', alt: 'Japanese Peace Pagoda' },
  jetavanaramaya: { src: jetavanaramayaSrc, position: '50% 50%', alt: 'Jetavanaramaya' },
  kalpitiyaPeninsula: { src: kalpitiyaPeninsulaSrc, position: '50% 50%', alt: 'Kalpitiya Peninsula' },
  kandyViewPoint: { src: kandyViewPointSrc, position: '50% 50%', alt: 'Kandy View Point' },
  keerimalaiSpring: { src: keerimalaiSpringSrc, position: '50% 50%', alt: 'Keerimalai Spring' },
  kelaniyaRajaMahaVihara: { src: kelaniyaRajaMahaViharaSrc, position: '50% 50%', alt: 'Kelaniya Raja Maha Vihara' },
  kithalEllaWaterfall: { src: kithalEllaWaterfallSrc, position: '50% 50%', alt: 'Kithal Ella Waterfall' },
  kithulgala: { src: kithulgalaSrc, position: '50% 50%', alt: 'Kithulgala' },
  abayagiriViharaya: { src: abayagiriViharayaSrc, position: '50% 50%', alt: 'Abayagiri Viharaya' },
  ambuluwawaTower: { src: ambuluwawaTowerSrc, position: '50% 50%', alt: 'Ambuluwawa Tower' },
  koneswaramTemple: { src: koneswaramTempleSrc, position: '50% 50%', alt: 'Koneswaram Temple' },
  kosgodaSeaTurtleConservationProject: { src: kosgodaSeaTurtleConservationProjectSrc, position: '50% 50%', alt: 'Kosgoda Sea Turtle Conservation Project' },
  liptonSeat: { src: liptonSeatSrc, position: '50% 50%', alt: 'Lipton Seat' },
  littleAdamsPeak: { src: littleAdamsPeakSrc, position: '50% 50%', alt: 'Little Adams Peak' },
  loversLeapWaterfall: { src: loversLeapWaterfallSrc, position: '50% 50%', alt: 'Lovers Leap Waterfall' },
  madihaBeach: { src: madihaBeachSrc, position: '50% 50%', alt: 'Madiha Beach' },
  mihintale: { src: mihintaleSrc, position: '50% 50%', alt: 'Mihintale' },
  moonPlains: { src: moonPlainsSrc, position: '50% 50%', alt: 'Moon Plains' },
  muthurajawelaMarsh: { src: muthurajawelaMarshSrc, position: '50% 50%', alt: 'Muthurajawela Marsh' },
  nagadepaPuranaVihara: { src: nagadepaPuranaViharaSrc, position: '50% 50%', alt: 'Nagadepa Purana Vihara' },
  nallurKandaswamyTemple: { src: nallurKandaswamyTempleSrc, position: '50% 50%', alt: 'Nallur Kandaswamy Temple' },
  nationalMaritimeMuseum: { src: nationalMaritimeMuseumSrc, position: '50% 50%', alt: 'National Maritime Museum' },
  parrotRockBridge: { src: parrotRockBridgeSrc, position: '50% 50%', alt: 'Parrot Rock Bridge' },
  pedroTeaEstate: { src: pedroTeaEstateSrc, position: '50% 50%', alt: 'Pedro Tea Estate' },
  pidurangala: { src: pidurangalaSrc, position: '50% 50%', alt: 'Pidurangala' },
  pointPedro: { src: pointPedroSrc, position: '50% 50%', alt: 'Point Pedro' },
  yapahuwaRockFortress: { src: yapahuwaRockFortressSrc, position: '50% 50%', alt: 'Yapahuwa Rock Fortress' },
}

/* Name → photo rules, first match wins. Substring patterns are deliberately
   loose so admin-added rows ("Sigiriya", "Galle Fort Ramparts") still match.
   Order matters: /elephant/ must run before the bare /\bella\b/ place match. */
const NAME_RULES = [
  [/sigiriya/, scenes.sigiriyaGround],
  [/tooth|dalada/, scenes.templeOfTooth],
  [/lighthouse/, scenes.galleLighthouse],
  [/galle/, scenes.galleFort],
  [/nine arch|9 arch|demodara/, scenes.nineArch],
  [/yala/, scenes.leopard],
  [/adam|sri pada/, scenes.adamsPeak],
  [/dambulla/, scenes.dambulla],
  [/nuwara eliya|clair|devon fall/, scenes.stClairsFalls],
  [/whale/, scenes.whaleWatching],
  [/mirissa|coconut tree/, scenes.coconutTreeHill],
  [/unawatuna|hikkaduwa|bentota|arugam/, scenes.hikkaduwaBeach],
  [/blue beach|nilwella|nilweli/, scenes.blueBeachIsland],
  [/trincomalee|nilaveli|pigeon island/, scenes.hikkaduwaCoral],
  [/pinnawala|elephant|udawalawe|minneriya/, scenes.elephant],
  [/wilpattu|wilpaththu/, scenes.wilpattu],
  [/knuckles/, scenes.knucklesRange],
  [/ella rock/, scenes.ellaRock],
  [/haritha kanda|green mountain|bopath/, scenes.harithaKanda],
  [/\bella\b/, scenes.nineArch],
  [/horton/, scenes.hortonPlains],
  [/polonnaruwa/, scenes.polonnaruwa],
  [/anuradhapura/, scenes.anuradhapura],
  [/stilt|koggala/, scenes.stiltFishing],
  [/bahirawakanda/, scenes.bahirawakanda],
  [/bambarakanda/, scenes.bambarakanda],
  [/tea museum/, scenes.ceylonTeaMuseum],
  [/lotus tower/, scenes.colomboLotusTower],
  [/delft island/, scenes.delftIsland],
  [/diyaluma/, scenes.diyalumaFalls],
  [/gangaramaya/, scenes.gangaramayaTemple],
  [/gregory lake/, scenes.gregoryLake],
  [/hakgala/, scenes.hakgalaBotanicalGarden],
  [/isurumuniya/, scenes.isurumuniya],
  [/jaffna fort/, scenes.jaffnaFort],
  [/jaffna public library/, scenes.jaffnaPublicLibrary],
  [/peace pagoda/, scenes.japanesePeacePagoda],
  [/jetavanaramaya/, scenes.jetavanaramaya],
  [/kalpitiya/, scenes.kalpitiyaPeninsula],
  [/kandy view/, scenes.kandyViewPoint],
  [/keerimalai/, scenes.keerimalaiSpring],
  [/kelaniya/, scenes.kelaniyaRajaMahaVihara],
  [/kithal ella/, scenes.kithalEllaWaterfall],
  [/kithulgala/, scenes.kithulgala],
  [/abayagiri/, scenes.abayagiriViharaya],
  [/ambuluwawa/, scenes.ambuluwawaTower],
  [/koneswaram/, scenes.koneswaramTemple],
  [/kosgoda|turtle/, scenes.kosgodaSeaTurtleConservationProject],
  [/lipton/, scenes.liptonSeat],
  [/little adam/, scenes.littleAdamsPeak],
  [/lover.*leap/, scenes.loversLeapWaterfall],
  [/madiha/, scenes.madihaBeach],
  [/mihintale/, scenes.mihintale],
  [/moon plain/, scenes.moonPlains],
  [/muthurajawela/, scenes.muthurajawelaMarsh],
  [/nagadepa/, scenes.nagadepaPuranaVihara],
  [/nallur/, scenes.nallurKandaswamyTemple],
  [/maritime museum/, scenes.nationalMaritimeMuseum],
  [/parrot rock/, scenes.parrotRockBridge],
  [/pedro tea/, scenes.pedroTeaEstate],
  [/pidurangala/, scenes.pidurangala],
  [/point pedro/, scenes.pointPedro],
  [/yapahuwa/, scenes.yapahuwaRockFortress],
]

/* Generic (non-landmark) shots reused for unmatched rows of a category —
   a real beach photo on an unmatched beach beats a drawn placeholder. Only
   categories with genuinely generic imagery get a pool; other heritage
   sites without a bundled photo keep the existing image_url/SVG fallback
   rather than wearing another landmark's photo. */
const CATEGORY_POOLS = {
  beach: [scenes.hikkaduwaBeach, scenes.hikkaduwaCoral, scenes.hikkaduwaDiving],
  wildlife: [scenes.elephant, scenes.leopard],
}

/* One representative scene per category — used for photo-thumbnail filter
   chips and interest tags. */
const CATEGORY_SCENES = {
  heritage: scenes.dambulla,
  religious: scenes.templeOfTooth,
  historical: scenes.galleFort,
  scenic: scenes.nineArch,
  wildlife: scenes.leopard,
  hiking: scenes.adamsPeak,
  'hill country': scenes.stClairsFalls,
  beach: scenes.hikkaduwaBeach,
  nature: scenes.elephant,
  culture: scenes.templeOfTooth,
  adventure: scenes.hikkaduwaDiving,
  food: scenes.galleFortAlt,
  history: scenes.galleFort,
}

/** The representative scene for a category/interest, or null. */
export function categoryScene(category) {
  return CATEGORY_SCENES[(category || '').toLowerCase()] || null
}

/**
 * The bundled photo for an attraction, or null when we don't have one.
 * Resolution: name match → category pool (rotated by id) → null.
 */
export function attractionPhoto(attraction) {
  if (!attraction) return null
  const name = (attraction.name || '').toLowerCase()
  for (const [pattern, photo] of NAME_RULES) {
    if (pattern.test(name)) return photo
  }
  const pool = CATEGORY_POOLS[(attraction.category || '').toLowerCase()]
  if (pool) return pool[(attraction.id || 0) % pool.length]
  return null
}
