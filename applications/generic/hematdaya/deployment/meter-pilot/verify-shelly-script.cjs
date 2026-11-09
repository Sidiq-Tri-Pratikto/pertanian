const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const test = require("node:test");
const { runInNewContext } = require("node:vm");

const deviceScript = readFileSync(join(__dirname, "shelly-plug-pm-gen3.js"), "utf8");
const meterId = "11111111-1111-4111-8111-111111111111";
const readingTime = 1_783_000_000;

function startDevice() {
  const state = {
    connected: true,
    clock: { unixtime: readingTime },
    meter: { aenergy: { total: 0 } },
  };
  const publications = [];
  const timers = [];
  runInNewContext(deviceScript.replace("REPLACE_WITH_METER_UUID", meterId), {
    MQTT: {
      isConnected: () => state.connected,
      publish: (topic, body, qos, retain) => publications.push({ topic, body: JSON.parse(body), qos, retain }),
    },
    Shelly: {
      getComponentStatus: (component, channel) => {
        if (component === "sys") return state.clock;
        assert.equal(component, "pm1");
        assert.equal(channel, 0);
        return state.meter;
      },
    },
    Timer: { set: (delay, repeat, tick) => timers.push({ delay, repeat, tick }) },
  });
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 60_000);
  assert.equal(timers[0].repeat, true);
  return { state, publications, tick: timers[0].tick };
}

test("publishes cumulative Wh once a minute, including zero and an unchanged counter", () => {
  const { state, publications, tick } = startDevice();
  state.clock.unixtime += 60;
  tick();
  state.clock.unixtime += 60;
  state.meter.aenergy.total = 12.375;
  tick();

  assert.deepEqual(
    publications,
    ["0.000", "0.000", "12.375"].map((energyWh, minute) => ({
      topic: `hematdaya/v1/meters/${meterId}/readings`,
      body: { measured_at: readingTime + minute * 60, energy_wh: energyWh },
      qos: 1,
      retain: false,
    })),
  );
});

test("does not send samples while disconnected, unsynced, or failing to measure", () => {
  const { state, publications, tick } = startDevice();
  state.connected = false;
  tick();
  state.connected = true;
  state.clock.unixtime = null;
  tick();
  state.clock.unixtime = readingTime + 60;
  state.meter.errors = ["power_meter_failure"];
  tick();
  state.meter = { aenergy: { total: Infinity } };
  tick();

  assert.equal(publications.length, 1);
});
