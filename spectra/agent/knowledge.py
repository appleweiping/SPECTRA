"""Shared interface/PDK descriptions and topology knowledge cards (all given to ALL LLM methods)."""

import hashlib
import json

PDK_SHEET = """PDK: SkyWater SKY130, 1.8 V core devices only, simulated with ngspice (BSIM4), nominal VDD = 1.8 V, 27 C.
Devices you may use inside the DUT (canonical netlist syntax, sizes in micrometres):
  M<name> <d> <g> <s> <b> nfet W=<um> L=<um> [m=<int>]   (NMOS; bulk MUST be vss = p-substrate)
  M<name> <d> <g> <s> <b> pfet W=<um> L=<um> [m=<int>]   (PMOS; bulk to vdd or its own source n-well)
  Q<name> <c> <b> <e> pnp [m=<int>]                       (substrate vertical PNP 3.4x3.4um; collector MUST be vss)
  R<name> <a> <b> <ohms>     C<name> <a> <b> <farads>      (ideal passives; e.g. 10k, 2p, 1.5e-12)
Limits: 0.42 <= W <= 5000 (total width), 0.15 <= L <= 20, m <= 200; 0.1 ohm <= R <= 1G; 0.1f <= C <= 1u.
No other elements (no ideal sources, no controlled sources, no inductors) inside the DUT.
Typical device facts (TT, 27 C, VDS=0.6 V):
  nfet: Vth ~ 0.60-0.66 V; at gm/Id=10 S/A: Id/W ~ 27 uA/um (L=0.15), 8.7 (L=0.5), 4.4 (L=1), 2.4 (L=2); intrinsic gain gm/gds ~ 17 (L=0.15), 80 (L=0.5), 124 (L=1), 150 (L=2)
  pfet: |Vth| ~ 0.95-1.0 V (high!); at gm/Id=10: Id/W ~ 5.1 uA/um (L=0.15), 2.2 (L=0.5), 1.15 (L=1), 0.56 (L=2); gm/gds ~ 8 (L=0.15), 84 (L=0.5), 229 (L=1), 340 (L=2); pfet gm/Id saturates near ~16
  pnp: Veb ~ 0.76 V at 10 uA, slope ~ -1.7 mV/C.
The circuit must be a single subcircuit named `dut` with EXACTLY the port list given in the task."""


FAMILY_IFACE = {
    "opamp": """Interface (.subckt dut vinp vinn vout vdd vss ibias): single-ended-output op-amp/OTA. Testbench: VDD on vdd, vss=0 V.
An ideal reference current IREF flows from VDD INTO pin `ibias` (you must sink it, e.g. diode-connected nfet to vss).
Inputs at common-mode VCM. Load capacitor CL on vout. Open-loop AC measured with a DC feedback servo (vout tied to vinn
through 1 GOhm, vinn AC-grounded by 1 F). Slew/settling measured as a unity-gain buffer with a step. Output swing measured
in an inverting gain-of-10 configuration (1 MOhm feedback). vinp must be the NON-inverting input.""",
    "amp": """Interface (.subckt dut vin vout vdd vss ibias): single-ended voltage amplifier. The testbench drives vin with a DC
level VIN_DC plus small AC; IREF flows from VDD INTO `ibias`. Load CL on vout. Gain is |vout/vin| at low frequency;
output DC level and swing (output range keeping >=50% of small-signal gain under a +-0.3 V input DC sweep) are measured.""",
    "tia": """Interface (.subckt dut iin vout vdd vss ibias): transimpedance amplifier. An AC current source drives iin
(DC input current 0) in parallel with a photodiode capacitance CPD to ground. IREF flows from VDD INTO `ibias`.
Load CL on vout. Transimpedance = |vout/iin| at low frequency (dB-ohm); bandwidth = -3 dB frequency.""",
    "cmirror": """Interface (.subckt dut iin iout vdd vss): current mirror. An ideal input current IIN always flows from VDD INTO
pin iin; the testbench holds iout at a DC voltage (swept 0..VDD). For direction=sink the output current is the current
flowing INTO iout; for direction=source it is the current flowing OUT of iout (compliance then refers to VDD minus the
highest output voltage). Measured: iout at VOUT_NOM, output resistance at VOUT_NOM, compliance voltage = lowest iout voltage at
which the current is still >= 95% of its value at VOUT_NOM. vdd may be left unused.""",
    "ldo": """Interface (.subckt dut vin vout vref vss ibias): low-dropout regulator. vin is the input supply (1.8 V), vref an ideal
reference voltage VREF, IREF flows from vin INTO `ibias`. Load: DC current sink ILOAD from vout to ground (stepped between
ILOAD_MIN and ILOAD_MAX with 100 ns edges for transient tests) plus capacitor CL. Measured: vout accuracy, load regulation
(V/A = mV/mA), line regulation (dVout/dVin), PSRR at 1 kHz, quiescent current at ILOAD_MIN, undershoot/overshoot and
residual ringing (peak-to-peak in the last 3 us of each load phase).""",
    "ref": """Interface (.subckt dut vdd vref vss): self-biased voltage reference (no external bias). vref drives 1 pF.
Measured: vref at 27 C, temperature coefficient (box method, -40..125 C, ppm/C), line regulation (dVref/dVdd over
VDD +- 0.2 V), supply current/power, PSRR at 1 kHz, and START-UP: VDD ramps 0->1.8 V in 10 us and vref must reach its DC
value within 40 us (include a start-up circuit if the core has a zero-current state).""",
    "comparator": """Interface (.subckt dut vinp vinn vout vdd vss ibias): continuous-time (unclocked) comparator; vout must be
rail-to-rail logic: HIGH when vinp > vinn. IREF flows from VDD INTO `ibias`. vinn = VCM; vinp steps between VCM-VOD and VCM+VOD.
Load CL. Measured: propagation delay (max of rising/falling, input step to vout crossing VDD/2), static power, input offset.""",
    "latch": """Interface (.subckt dut vinp vinn clk outp outn vdd vss): clocked comparator. clk is a rail-to-rail clock at FCLK
(clk HIGH = evaluate, LOW = reset). Input differential +-DV around VCM. At the end of each evaluation phase outp must be
>0.9*VDD and outn <0.1*VDD when vinp>vinn (and vice-versa); during reset both outputs must return to the same level.
Measured: correctness, delay (clk rising edge to |outp-outn| > VDD/2), energy per comparison. Loads CL on outputs.""",
    "vco": """Interface (.subckt dut vctrl vout vdd vss): voltage-controlled oscillator with rail-to-rail-ish output on vout
(load CL). Measured by transient at three control voltages (low, mid, high of VCTRL_RANGE): oscillation frequency at each,
tuning ratio fmax/fmin, gain Kvco, minimum output peak-to-peak swing, average power at mid control voltage. A small kick
current is injected at t=0 to start oscillation.""",
    "filter": """Interface (.subckt dut vin vout vdd vss ibias): active filter; vin is driven at DC = VCM = 0.9 V plus AC.
IREF flows from VDD INTO `ibias`. Load CL. For low-pass: passband gain (at 10 Hz), -3 dB cutoff fc, peaking above passband,
attenuation at STOP_RATIO*fc. For band-pass: centre frequency f0, peak gain, quality factor Q. Static power.""",
    "schmitt": """Interface (.subckt dut vin vout vdd vss): Schmitt trigger. vin ramps slowly 0->VDD->0 (20 us); upper threshold
vth_hi (rising input where vout crosses VDD/2), lower threshold vth_lo, hysteresis = vth_hi - vth_lo; output must be rail-to-rail.
Non-inverting unless stated (vout HIGH for high vin).""",
    "opamp_app": """Interface (.subckt dut vin1 vin2 vout vcm vdd vss ibias): closed-loop op-amp circuit (you design the op-amp
AND the feedback network). vcm is an ideal 0.9 V reference node you may use as signal ground. vin1/vin2 are driven at DC = 0.9 V
plus AC. IREF flows from VDD INTO `ibias`. Load CL. Measured: low-frequency signed gains a1 = dvout/dvin1, a2 = dvout/dvin2,
closed-loop bandwidth, output DC offset from 0.9 V, power; for integrators the unity-gain frequency and slope.""",
}

# Topology knowledge cards (shared by ALL LLM methods: SPECTRA and baselines; design intent, trade-offs, analytic models)
KNOWLEDGE = {
    "opamp": """Topology cards (analytic models in terms of gm, gds; use LUT gm/Id design):
[5T-OTA] diff pair + mirror load. A0=gm1/(gds2+gds4); GBW=gm1/(2*pi*CL); single dominant pole -> PM~90 deg if mirror pole
 (gm3/(2*Cgs3)) >> GBW. Gain typically 30-45 dB in sky130 (raise L for more). Very low power option.
[Two-stage Miller] A0=gm1/(gds2+gds4)*gm7/(gds7+gds8) (60-85 dB). GBW=gm1/(2*pi*Cc). p2~gm7/CL -> need gm7 > ~2.2*gm1*CL/Cc
 for PM 60; nulling resistor Rz~1/gm7 (or >) cancels RHP zero. SR=min(Itail/Cc, I7/(CL+Cc)). Best swing.
[Folded cascode] single stage, A0~gm1*Rout with cascodes (60-75 dB), GBW=gm1/(2*pi*CL), excellent PM, needs cascode bias;
 swing limited by 4 Vdsat; PMOS current sources must carry Itail/2 + cascode branch current.
[Telescopic] highest speed/efficiency, poor swing at 1.8 V (pfet Vth ~1 V!).
[Folded-cascode + CS 2nd stage / cascoded Miller] >85 dB gain with Miller or Ahuja (cascode) compensation.
sky130 tips: pfet |Vth|~1 V limits PMOS-input headroom: prefer NMOS input pair for VCM=0.9 V. Long L (0.5-2 um) for gain on
loads/mirrors, short-ish L on input pair for speed. Input pair gm/Id 12-18 (efficiency), mirrors/current sources gm/Id 6-10.""",
    "amp": """[CS + current-source load] A=gm1/(gds1+gds2) high gain but output DC very sensitive -> size so Id1(VIN_DC)=Id2.
[CS + diode load] A~gm1/gm2 (robust, low gain ~ sqrt(mu_n W1/L1 / mu_p W2/L2)). [Cascode] A~gm1*(gm2 ro2 ro1 || gm3 ro3 ro4).
[Source follower] A~gm/(gm+gmb) < 1, wide BW, vout = vin - VGS. Bandwidth ~ 1/(2*pi*Rout*CL). Output DC must lie mid-rail.""",
    "tia": """[Shunt-feedback TIA] Zt~Rf*A/(1+A); BW~(1+A)/(2*pi*Rf*Cin) limited by amplifier pole; need A>>1 and phase margin;
source follower output buffer isolates CL. Noise ~ 4kT/Rf. [Common-gate/RGC] low input impedance for large CPD.""",
    "cmirror": """[Simple] Rout=ro, compliance=Vdsat. [Cascode stack] Rout~gm*ro^2, compliance=Vth+2Vdsat (high).
[Wide-swing/self-biased cascode] series resistor R sets cascode bias: compliance ~2Vdsat with Rout~gm ro^2.
Long L improves ro and matching; ratio by W or m (prefer m for accuracy). PMOS output stage for source mirrors.""",
    "ldo": """[PMOS-pass LDO] error amp (OTA) drives pass-device gate; feedback divider sets Vout=Vref(1+R1/R2).
Loop gain ~ A_ea*gm_pass*Rout_eff; dominant pole at gate (Miller Cc gate->vout) or output (large CL). Pass device must
deliver ILOAD_MAX with VSG <= VIN - Vgate_min: W very large (hundreds-thousands um), L=0.15-0.3. Load regulation ~ 1/(loop gain*gm_pass)...
Quiescent current dominated by error amp + divider. Watch stability across load (gm_pass varies with ILOAD).""",
    "ref": """[Op-amp-less CMOS bandgap] PNP pair 1:N, NMOS level-shift pair forces equal emitter voltages, PMOS mirror:
I = UT*ln(N)/R1 (PTAT). Vref = Veb3 + (R2/R1)*UT*ln(N); choose R2/R1*ln(N)*UT ~ 0.5-0.6 V so the PTAT slope (~ +R2/R1*ln N*0.086 mV/C)
cancels Veb slope (-1.7 mV/C). Vref ~ 1.15-1.25 V. Needs start-up (pull PMOS gate low when vref low).
[MOS-only / subthreshold refs] lower power, worse TC. Cascode mirrors improve line regulation.""",
    "comparator": """[Preamp + gain stage + inverter] OTA preamp then CS stage then inverter for rail-to-rail; delay ~ sum of stage slewing;
power from bias currents. Polarity: vout HIGH when vinp > vinn. Systematic offset from mismatch of stage DC levels.""",
    "latch": """[StrongARM] tail switch on clk, input pair, cross-coupled inverters, PMOS reset switches on all internal nodes,
output inverters. Delay ~ (CL/gm_latch)*ln(VDD/(Av*DV)); energy ~ total switched capacitance * VDD^2.
[Double-tail] separate preamp/latch tails for low-voltage operation.""",
    "vco": """[Current-starved ring] odd N stages; f ~ I/(N*Ctot*VDD); vctrl sets starving current (NMOS starving, PMOS mirrored).
Fewer stages -> higher f. [Simple inverter ring + supply control]. Keep swing near rail-to-rail.""",
    "filter": """[Sallen-Key unity-gain LPF] w0=1/sqrt(R1R2C1C2), Q=sqrt(R1R2C1C2)/(C2(R1+R2)); Butterworth Q=0.707.
[3rd-order] RC pole + SK biquad. [MFB band-pass] f0=1/(2pi sqrt(R1||R2 * R3 C1 C2)) (C1=C2: Q=0.5 sqrt(R3/(R1||R2))).
Op-amp GBW must be >> f0*Q (>~20x). Op-amp output must handle the resistive load.""",
    "schmitt": """[6T CMOS Schmitt] feedback devices M3/M6 set thresholds: larger feedback widths -> larger hysteresis.
vth_hi increases with Wnf/Wn; vth_lo decreases with Wpf/Wp. Add an output inverter for polarity/drive.""",
    "opamp_app": """Use a robust two-stage Miller op-amp (gain >60 dB, PM >60 deg into the feedback load). Gains: inverting -Rf/R1,
non-inverting 1+Rf/Rg, summing -Rf/Ri per input, difference Rf/R1 with matched R3/R4. Closed-loop BW ~ GBW*beta.
Integrator: f_unity = 1/(2 pi R C); add a large resistor across C for a DC operating point. Resistors load the op-amp output:
keep them >= ~10 kOhm or provide output drive.""",
}


# Quantitative cards are retrieved from observations rather than pasted as one
# large family paragraph on every iteration.  The cards intentionally contain
# first-order relations and actions only.  They never contain a reference
# design, hidden optimum, or benchmark answer.
_CARD_RULES = {
    "opamp": [
        ("phase_pole", ("pm", "ugbw"), ("edge-of-saturation",), "p2≈gm7/(2πCL); increase Cc or gm7 and set Rz≈1/gm7", "check compensation and non-dominant pole"),
        ("gain_ro", ("gain_db",), (), "A0≈gm1ro1·gm7ro7; longer L raises ro", "increase L on high-impedance devices"),
        ("headroom", ("swing",), ("triode", "edge-of-saturation"), "Vds−Vdsat must stay positive at the output stack", "raise gm/Id or reduce stacked headroom"),
    ],
    "amp": [
        ("gain_ro", ("gain_db",), (), "A≈gmro for a common-source stage", "increase L or gm while preserving output bias"),
        ("bandwidth_gm", ("f3db", "gbw"), (), "f−3dB follows gm/(2πCL)", "raise gm or reduce effective capacitance"),
        ("output_headroom", ("swing", "vout_dc"), ("triode",), "output devices need Vds−Vdsat margin", "rebias the output node or raise gm/Id"),
    ],
    "tia": [
        ("feedback_bandwidth", ("f3db",), (), "Zt bandwidth is limited by (1+A)/(2πRfCin)", "reduce Rf/Cin or increase loop gain"),
        ("transimpedance", ("zt_dbohm",), (), "Zt≈Rf·A/(1+A)", "increase loop gain before raising Rf"),
        ("noise", ("in_noise_1m",), (), "resistor and input-device noise set the floor", "balance Rf and input gm under the power limit"),
    ],
    "cmirror": [
        ("compliance", ("v_compliance",), ("triode", "edge-of-saturation"), "compliance is set by the output Vdsat stack", "raise gm/Id or use a wide-swing cascode"),
        ("output_resistance", ("rout",), (), "Rout≈gm·ro² for a cascode", "increase L while retaining headroom"),
        ("matching_ratio", ("iout_err_pct",), (), "matched L and m preserve the mirror ratio", "use shared intent variables for matched devices"),
    ],
    "ldo": [
        ("loop_stability", ("ripple_settled", "undershoot", "overshoot"), (), "loop pole/zero placement controls settling", "retune Cc and the gate/output pole"),
        ("load_regulation", ("load_reg", "line_reg"), (), "loop gain≈Aea·gm_pass·Rout", "increase error-amplifier gain or pass gm"),
        ("dropout_drive", ("vout_err_pct",), ("triode",), "pass-device Vdsat consumes dropout headroom", "increase pass width and preserve gate swing"),
    ],
    "ref": [
        ("startup", ("startup_ok",), (), "self-biased references need a transient startup path", "add a weak startup branch that turns off in steady state"),
        ("temperature", ("tc_ppm",), (), "PTAT and CTAT slopes should cancel", "rebalance resistor ratio and device area ratio"),
        ("line_psrr", ("line_reg", "psrr_1k"), (), "cascoded mirrors improve supply rejection", "increase output resistance with available headroom"),
    ],
    "filter": [
        ("cutoff", ("fc", "f0"), (), "w0≈1/sqrt(R1R2C1C2)", "scale the RC product to move the pole"),
        ("quality_factor", ("q", "peaking_db"), (), "Q is controlled by the resistor/capacitor ratio", "retune the damping ratio"),
        ("active_drive", ("gain_db",), (), "the op-amp GBW should exceed f0·Q", "increase gm or lower the target pole"),
    ],
    "vco": [
        ("tuning", ("tuning_ratio", "kvco", "fmin", "fmax"), (), "ring frequency follows I/(NCVDD)", "move the control device between weak and moderate inversion"),
        ("swing", ("swing",), (), "buffer gain and current determine rail-to-rail swing", "increase the final-stage drive"),
        ("power", ("power",), (), "dynamic power≈CVDD²f plus bias current", "reduce switched capacitance or bias current"),
    ],
    "comparator": [
        ("delay", ("tpd",), (), "delay is dominated by slewing and regenerative gm", "increase input/latch gm under the power budget"),
        ("offset", ("offset",), (), "matched input devices reduce systematic offset", "share intent variables and equalize operating regions"),
        ("polarity", ("polarity_ok",), (), "input polarity must map to the required output state", "check the differential pair and inverter orientation"),
    ],
    "latch": [
        ("regeneration", ("correct", "delay"), (), "regeneration time scales with CL/gm", "increase latch gm and reset margin"),
        ("reset", ("correct",), (), "reset devices must equalize internal nodes", "strengthen reset paths without upsetting the tail"),
        ("energy", ("energy",), (), "switching energy≈CswVDD²", "reduce unnecessary internal capacitance"),
    ],
    "schmitt": [
        ("thresholds", ("vth_hi", "vth_lo", "hysteresis"), (), "feedback-device ratios set the two thresholds", "adjust the positive-feedback widths"),
        ("swing", ("power_avg",), (), "rail-to-rail inverter drive controls transition quality", "balance pull-up and pull-down strength"),
    ],
    "opamp_app": [
        ("closed_loop_gain", ("a1", "a2"), (), "closed-loop gain follows resistor ratios", "match the feedback ratio to the requested signed gain"),
        ("closed_loop_bw", ("bw", "f_unity"), (), "closed-loop bandwidth≈GBW·β", "increase op-amp gm or feedback bandwidth"),
        ("offset", ("vout_offset",), (), "input mismatch and bias imbalance shift the DC output", "rebalance matched branches and bias currents"),
    ],
}


def _build_cards():
    cards = []
    for family, rules in _CARD_RULES.items():
        for cid, metrics, regions, formula, action in rules:
            card = {"id": f"{family}.{cid}", "family": family, "metrics": list(metrics),
                    "regions": list(regions), "formula": formula, "action": action,
                    "source": "SPECTRA-knowledge-v1", "version": 1}
            payload = json.dumps(card, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            card["sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            cards.append(card)
    return tuple(cards)


CARD_INDEX = _build_cards()


def retrieve_cards(task, analysis=None, limit=3):
    """Retrieve cards using only the task family and observed failure evidence."""
    family = task.get("family")
    analysis = analysis or {}
    failed = {x.get("metric") for x in analysis.get("failing", [])}
    regions = {x.get("region") for x in analysis.get("flags", [])}
    ranked = []
    for card in CARD_INDEX:
        if card["family"] != family:
            continue
        metric_hits = len(failed & set(card["metrics"]))
        region_hits = len(regions & set(card["regions"]))
        # Cards matching an observed violation are preferred.  Stable ID tie
        # breaking makes retrieval reproducible across workers and seeds.
        score = 4 * metric_hits + 2 * region_hits
        ranked.append((score, card["id"], card))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    selected = [dict(card, retrieval_score=score) for score, _, card in ranked[:limit] if score > 0]
    if selected:
        return selected
    return [dict(card, retrieval_score=0) for _, _, card in ranked[:limit]]


def render_cards(cards):
    """Render retrieved cards for the iterate prompt without hidden state."""
    if not cards:
        return "(no retrieved cards; use only the interface, PDK and observed simulation evidence)"
    lines = []
    for c in cards:
        digest = str(c.get("sha256", "unhashed"))[:12]
        lines.append(f"- [{c['id']}] {c['formula']}. Action: {c['action']} "
                     f"(source={c.get('source', 'unknown')} v{c.get('version', '?')} sha256={digest})")
    return "\n".join(lines)
