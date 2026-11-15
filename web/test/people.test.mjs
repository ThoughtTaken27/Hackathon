import test from "node:test";
import assert from "node:assert/strict";
import { RELATIONS, ROOMS, NAME_CHIPS, personName, possessive, roomName, place, caregiverName, normaliseNames } from "../public/js/people.js";

const rels = Object.keys(RELATIONS), rooms = Object.keys(ROOMS);
const roomOf = (type) => (type === "other" ? { type, name: "workshop" } : { type });

test("every relationship x room x viewer gives a clean title", () => {
  for (const relation of rels) for (const type of rooms) {
    const names = { relation };
    const rn = roomName(roomOf(type));
    const lead = relation === "self" ? "Your" : RELATIONS[relation] + "'s";
    assert.equal(place(names, roomOf(type), "family"), `${lead} ${rn}`);
    assert.equal(place(names, roomOf(type), "person"), `Your ${rn}`);
    assert.equal(place(names, roomOf(type), "person", { mid: true }), `your ${rn}`);
    const mid = relation === "self" ? "your" : RELATIONS[relation].replace("Your ", "your ") + "'s";
    assert.equal(place(names, roomOf(type), "family", { mid: true }), `${mid} ${rn}`);
    assert.ok(!/\b(he|she|his|him|her)\b/i.test(place(names, roomOf(type))));
  }
});

test("known titles", () => {
  assert.equal(place({ parent: "Mom", relation: "parent" }, { type: "bedroom" }), "Mom's bedroom");
  assert.equal(place({}, { type: "kitchen" }), "Your parent's kitchen");
  assert.equal(place({}, { type: "kitchen" }, "family", { mid: true }), "your parent's kitchen");
  assert.equal(place({ relation: "self" }, { type: "living" }), "Your living room");
  assert.equal(place({ parent: "Mom" }, { type: "bathroom" }), "Mom's bathroom");
  assert.equal(place({ parent: "Mom" }, { type: "other", name: "Sunroom" }), "Mom's Sunroom");
});

test("personName start and mid", () => {
  for (const r of rels) {
    assert.equal(personName({ relation: r }), RELATIONS[r]);
    assert.equal(personName({ relation: r }, { mid: true }), r === "self" ? "you" : RELATIONS[r].replace("Your ", "your "));
  }
  assert.equal(personName({ parent: "  Nani ", relation: "grandparent" }, { mid: true }), "Nani");
  assert.equal(personName({ parent: "   " }), "Your parent");
  assert.equal(personName(undefined), "Your parent");
});

test("possessive", () => {
  assert.equal(possessive("Mom"), "Mom's");
  assert.equal(possessive("James"), "James's");
  assert.equal(possessive("Your parent"), "Your parent's");
  assert.equal(possessive("your parent"), "your parent's");
  assert.equal(possessive("You"), "Your");
  assert.equal(possessive("you"), "your");
  assert.equal(place({ parent: "James" }, { type: "hallway" }), "James's hallway");
});

test("non-English names", () => {
  assert.equal(place({ parent: "Nani" }, { type: "kitchen" }), "Nani's kitchen");
  assert.equal(place({ parent: "Abuelo" }, { type: "living" }, "family"), "Abuelo's living room");
  assert.deepEqual(NAME_CHIPS, [...NAME_CHIPS].sort((a, b) => a.localeCompare(b)));
});

test("caregiverName", () => {
  assert.equal(caregiverName({ caregiver: "Meera" }, "family"), "Meera");
  assert.equal(caregiverName({ caregiver: "Meera" }, "person"), "Meera");
  assert.equal(caregiverName({}, "family"), "you");
  assert.equal(caregiverName({}, "person"), "your family");
  assert.equal(caregiverName(null, "person"), "your family");
});

test("old homes keep working", () => {
  const old = { parent: "Dad", caregiver: "Meera" };
  assert.equal(place(old, undefined), "Dad's kitchen");
  assert.equal(place(old, undefined, "person"), "Your kitchen");
  assert.deepEqual(normaliseNames(old), { parent: "Dad", caregiver: "Meera", relation: "parent" });
  assert.deepEqual(normaliseNames(null), { parent: null, caregiver: null, relation: "parent" });
  assert.equal(roomName({ type: "nonsense" }), "kitchen");
});

test("room profiles are complete", () => {
  for (const r of Object.values(ROOMS)) {
    assert.ok(r.label && r.name && r.teach.length >= 2 && r.placement.length === 4 && r.privacy && r.defaultChecks.length);
    assert.equal(r.measured, r.id === "kitchen");
  }
  assert.equal(ROOMS.bathroom.showsSounds, false);
  assert.deepEqual(ROOMS.bathroom.sounds, []);
  assert.equal(ROOMS.bedroom.showsActivities, false);
});
