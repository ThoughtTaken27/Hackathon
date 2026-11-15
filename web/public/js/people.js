// Who Kettle is for and which room it listens in. Pure data and string helpers, no DOM: used by every screen, the Worker and the tests.
export const RELATIONS = { parent: "Your parent", grandparent: "Your grandparent", partner: "Your partner", relative: "Your relative", friend: "Your friend", self: "You" };
export const RELATION_LABELS = { parent: "My parent", grandparent: "My grandparent", partner: "My partner", relative: "Another relative", friend: "A friend or neighbour", self: "Myself" };
export const NAME_CHIPS = ["Abuela", "Abuelo", "Amma", "Appa", "Dad", "Dadi", "Grandma", "Grandpa", "Mom", "Mum", "Nana", "Nani"];

const ALL_SOUNDS = ["kettle", "frying", "chopping", "blender", "microwave", "dishes", "tap", "cupboard", "doorbell", "tv", "music", "talking", "vacuum", "footsteps", "door", "alarm_clock", "knock", "keys"];
const step = (c, head, body, s) => ({ c, head, body, s });
const quiet = step("quiet", "Stay quiet", "Let Kettle hear the room as it usually is.", 10);

export const ROOMS = {
  kitchen: { id: "kitchen", name: "kitchen", label: "Kitchen", showsActivities: true, showsSounds: true,
    sounds: ["kettle", "frying", "chopping", "blender", "microwave", "dishes", "tap", "cupboard", "doorbell"],
    defaultChecks: [{ type: "activity_by", time: "10:00" }, { type: "concern", id: "no_meal", time: "14:00" }, { type: "concern", id: "stove" }, { type: "concern", id: "water" }],
    teach: [quiet, step("wash", "Wash up or run the tap", "Run the tap or clink a few dishes.", 10), step("cook", "Cook or pretend to", "Fry, chop or stir for a few seconds.", 10)],
    placement: ["Put it near the stove and sink, where the sounds are.", "Keep it away from the TV.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Kettle names the kind of sound, like dishes or frying, and forgets the sound.", measured: true },
  living: { id: "living", name: "living room", label: "Living room", showsActivities: true, showsSounds: true,
    sounds: ["tv", "music", "talking", "vacuum", "footsteps", "door"],
    defaultChecks: [{ type: "tv_over", hours: 8 }, { type: "concern", id: "tv_night" }, { type: "concern", id: "too_quiet" }],
    teach: [quiet, step("tv", "Turn the TV on", "Play the TV at a normal volume.", 10), step("move", "Talk or move about", "Talk, or walk across the room.", 10)],
    placement: ["Put it on a shelf or table with a clear view of the room.", "Keep it a few steps from the TV speaker.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Kettle names the kind of sound, like TV or talking, and never keeps words.", measured: false },
  bedroom: { id: "bedroom", name: "bedroom", label: "Bedroom", showsActivities: false, showsSounds: true,
    sounds: ["alarm_clock", "footsteps", "door", "tv"],
    defaultChecks: [{ type: "activity_by", time: "09:00" }, { type: "concern", id: "night" }],
    teach: [quiet, step("walk", "Get up and walk", "Stand up and walk a few steps.", 10), step("drawer", "Open a drawer or door", "Open and close a drawer or the door.", 10)],
    placement: ["On a dresser, not the nightstand by the bed, so breathing and snoring are quieter.", "Point the screen toward the room, not the bed.", "Plug it in so the battery lasts.", "Dim the screen at night."],
    privacy: "Kettle shows an activity level, not the sounds. Breathing, snoring and talking are never named or sent.", measured: false },
  hallway: { id: "hallway", name: "hallway", label: "Hallway or front door", showsActivities: false, showsSounds: true,
    sounds: ["door", "doorbell", "knock", "footsteps", "keys"],
    defaultChecks: [{ type: "concern", id: "too_quiet" }],
    teach: [quiet, step("walk", "Walk through", "Walk past the device a few times.", 10), step("door", "Open and close the front door", "Open the door and close it.", 10)],
    placement: ["Put it near the front door, on a shelf or table.", "Keep it out of the way of feet.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Kettle shows an activity level and door sounds. It never names voices or words.", measured: false },
  bathroom: { id: "bathroom", name: "bathroom", label: "Bathroom (safety only)", showsActivities: false, showsSounds: false,
    sounds: [],
    defaultChecks: [{ type: "concern", id: "water" }],
    teach: [quiet, step("tap", "Run the tap", "Run the tap for a few seconds.", 10)],
    placement: ["Keep it dry, on a shelf away from the sink and shower.", "Many families prefer the hallway outside.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Toilet, shower and body sounds are never named or sent. Only safety alerts.", measured: false },
  home: { id: "home", name: "home", label: "Whole small home or studio", showsActivities: true, showsSounds: true,
    sounds: ALL_SOUNDS,
    defaultChecks: [{ type: "activity_by", time: "10:00" }, { type: "concern", id: "too_quiet" }],
    teach: [quiet, step("move", "Move about", "Walk around and do something usual.", 10), step("door", "Use a door or drawer", "Open and close a door or drawer.", 10)],
    placement: ["Put it where it can hear most of the home, like a central shelf.", "Keep it away from the TV.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Kettle names the kind of sound and forgets the sound. It never keeps words.", measured: false },
  other: { id: "other", name: "room", label: "Other", showsActivities: true, showsSounds: true,
    sounds: ALL_SOUNDS,
    defaultChecks: [{ type: "activity_by", time: "10:00" }, { type: "concern", id: "too_quiet" }],
    teach: [quiet, step("move", "Move about", "Walk around and do something usual.", 10), step("door", "Use a door or drawer", "Open and close a door or drawer.", 10)],
    placement: ["Put it where it can hear the room, on a shelf or table.", "Keep it away from the TV.", "Plug it in so the battery lasts.", "Keep the screen on and Kettle open."],
    privacy: "Kettle names the kind of sound and forgets the sound. It never keeps words.", measured: false },
};

export const DEFAULT_NAMES = { parent: null, caregiver: null, relation: "parent" };
const clean = (s) => (typeof s === "string" && s.trim() ? s.trim() : null);

export function normaliseNames(n) {
  const x = n || {};
  return { parent: clean(x.parent), caregiver: clean(x.caregiver), relation: RELATIONS[x.relation] ? x.relation : "parent" };
}

export function personName(names, { mid = false } = {}) {
  const x = normaliseNames(names);
  const base = x.parent || RELATIONS[x.relation];
  if (!mid || x.parent) return base;
  return base === "You" ? "you" : base.replace(/^Your /, "your ");
}

export function possessive(name) {
  if (name === "You") return "Your";
  if (name === "you") return "your";
  return `${name}'s`;
}

export function roomName(room) {
  const type = room && ROOMS[room.type] ? room.type : "kitchen";
  const custom = type === "other" && room && clean(room.name);
  return custom || ROOMS[type].name;
}

export function place(names, room, viewer = "family", { mid = false } = {}) {
  if (viewer === "person") return `${mid ? "your" : "Your"} ${roomName(room)}`;
  return `${possessive(personName(names, { mid }))} ${roomName(room)}`;
}

export function caregiverName(names, viewer) {
  return clean(names && names.caregiver) || (viewer === "family" ? "you" : "your family");
}

/**
 * Everything a screen needs to name the person and the room, from the stored names ({parent, caregiver, relation, room}).
 * Before setup (or with no name) this is neutral: "Your parent", "your parent's room", never "Mom" or "Dad".
 * room is { type: "kitchen" | "living" | "bedroom" | ..., name } (people.js ROOMS); no room = kitchen (older homes).
 */
export function who(names, viewer = "family") {
  const x = normaliseNames(names), room = names && names.room;
  const name = personName(x), mid = personName(x, { mid: true });
  const type = room && ROOMS[room.type] ? room.type : "kitchen";
  return { parent: name, parentMid: mid, poss: possessive(name), possMid: possessive(mid), room: roomName(room), roomType: type,
    roomLabel: type === "other" ? roomName(room).replace(/^./, (c) => c.toUpperCase()) : ROOMS[type].label,
    place: place(x, room, viewer === "person" ? "person" : "family"), placeMid: place(x, room, viewer === "person" ? "person" : "family", { mid: true }),
    caregiver: caregiverName(names, viewer), Caregiver: caregiverName(names, viewer).replace(/^./, (c) => c.toUpperCase()), caregiverSet: !!clean(names && names.caregiver), self: x.relation === "self",
    relation: x.relation, roomObj: { type, name: type === "other" ? roomName(room) : "" } };
}
