// src/visual/glRenderer.js

const VERTEX_SHADER = `
  attribute vec2 a_pos;
  varying vec2 v_uv;

  void main() {
    v_uv = (a_pos + 1.0) * 0.5;
    gl_Position = vec4(a_pos, 0.0, 1.0);
  }
`;

const FRAGMENT_SHADER = `
  precision mediump float;

  uniform vec2 u_resolution;
  uniform float u_time;
  uniform float u_tension;
  uniform float u_entropy;
  uniform float u_curiosity;
  uniform float u_trust;
  uniform float u_fear;
  uniform float u_stability;
  uniform vec3 u_baseColor;
  uniform vec3 u_accentColor;
  uniform float u_cinematic;
  uniform vec3 u_longMemory;
  uniform vec2 u_continentSeed;
  uniform vec4 u_midMemory;
  uniform vec4 u_epochA;
  uniform vec4 u_epochB;
  uniform vec2 u_epochSeedA;
  uniform vec2 u_epochSeedB;
  uniform vec3 u_daily;

  varying vec2 v_uv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
  }

  float fbm(vec2 p) {
    float sum = 0.0;
    float amp = 0.55;
    for (int i = 0; i < 4; i++) {
      sum += amp * noise(p);
      p *= 2.0;
      amp *= 0.5;
    }
    return sum;
  }

  float ridged(vec2 p) {
    float n = fbm(p);
    n = 1.0 - abs(n * 2.0 - 1.0);
    return n * n;
  }

  vec3 epochColor(vec3 e) {
    vec3 color = vec3(0.08, 0.22, 0.35);
    color += vec3(0.45, 0.18, 0.12) * e.x;
    color += vec3(0.08, 0.35, 0.18) * e.y;
    color += vec3(0.1, 0.4, 0.5) * e.z;
    return clamp(color, 0.0, 1.0);
  }

  vec3 rotateY(vec3 v, float a) {
    float s = sin(a);
    float c = cos(a);
    return vec3(c * v.x + s * v.z, v.y, -s * v.x + c * v.z);
  }

  vec3 rotateX(vec3 v, float a) {
    float s = sin(a);
    float c = cos(a);
    return vec3(v.x, c * v.y - s * v.z, s * v.y + c * v.z);
  }

  float continentMask(vec3 n, vec3 center, vec2 seed, float radius, float soft, float jagged) {
    vec3 up = abs(center.y) > 0.8 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
    vec3 x = normalize(cross(up, center));
    vec3 y = cross(center, x);
    vec2 p = vec2(dot(n, x), dot(n, y));

    float n1 = fbm(p * (2.2 + jagged * 2.2) + seed * 6.0);
    float n2 = ridged(p * (3.4 + jagged * 3.2) + seed * 9.0);
    float mixN = mix(n1, n2, 0.35 + jagged * 0.35);

    float threshold = radius + (mixN - 0.5) * (0.06 + jagged * 0.09);
    float base = dot(n, center);
    return smoothstep(threshold, threshold + soft, base);
  }

  float starfield(vec2 p, float density, float seed) {
    vec2 ip = floor(p);
    vec2 fp = fract(p) - 0.5;
    float h = hash(ip + seed);
    float star = step(1.0 - density, h);
    float glow = smoothstep(0.5, 0.0, length(fp));
    float twinkle = 0.7 + 0.3 * sin(u_time * (0.4 + h * 2.3) + h * 6.2831);
    return star * glow * twinkle;
  }

  void main() {
    vec2 uv = v_uv * 2.0 - 1.0;
    uv.x *= u_resolution.x / u_resolution.y;

    float t = u_time * (0.04 + u_curiosity * 0.1);
    float grad = clamp((uv.y + 1.0) * 0.5, 0.0, 1.0);
    vec3 bg = mix(vec3(0.005, 0.01, 0.02), vec3(0.035, 0.05, 0.09), grad);
    float nebula = fbm(uv * 1.35 + vec2(t, -t));
    bg += vec3(0.02, 0.04, 0.08) * nebula * (0.2 + u_curiosity * 0.3);

    vec2 starUv = uv * 36.0;
    float stars = starfield(starUv, 0.02, 12.3);
    stars += starfield(starUv * 1.6, 0.03, 42.7);
    bg += vec3(0.8, 0.9, 1.0) * stars;

    float haze = fbm(uv * 1.9 + vec2(-t * 0.6, t * 0.35));
    haze *= smoothstep(1.1, 0.25, length(uv));
    bg += vec3(0.015, 0.05, 0.09) * haze * (0.25 + u_curiosity * 0.3);

    float edge = 0.62;
    float r = length(uv);

    float surfaceNoise = fbm(uv * (2.6 + u_entropy * 4.5) + u_time * (0.03 + u_tension * 0.08));
    float wobble = surfaceNoise * (0.015 + u_tension * 0.05) * (1.0 - u_stability);
    float planetMask = smoothstep(edge, edge - 0.015, r + wobble);

    vec3 color = bg;

    if (planetMask > 0.0) {
      float scaledR = r / edge;
      float z = sqrt(clamp(1.0 - scaledR * scaledR, 0.0, 1.0));
      vec3 normal = normalize(vec3(uv / edge, z));
      vec3 viewDir = vec3(0.0, 0.0, 1.0);

      float daily = clamp(u_daily.x + u_daily.y * 0.6, -1.0, 1.0);
      float storm = clamp(-daily, 0.0, 1.0);
      float flora = clamp(daily, 0.0, 1.0);

      float spin = u_time * (0.06 + u_curiosity * 0.05);
      float tilt = 0.22 + u_midMemory.z * 0.06 + storm * 0.03;
      float jitter = storm * 0.022 * sin(u_time * 1.5 + u_continentSeed.y * 5.0);
      spin += jitter;
      vec3 surfaceNormal = rotateY(rotateX(normal, tilt), spin);
      vec3 cloudNormal = rotateY(rotateX(normal, tilt), spin * 1.25);

      float lightAngle = u_time * 0.015 + u_continentSeed.x * 2.2;
      vec3 lightDir = normalize(vec3(cos(lightAngle) * 0.55, 0.2, 0.8));

      float diff = clamp(dot(surfaceNormal, lightDir), 0.0, 1.0);
      float wrap = 0.25;
      float lit = clamp((diff + wrap) / (1.0 + wrap), 0.0, 1.0);
      float dayShift = daily * 0.16;
      float night = smoothstep(-0.08 - dayShift, 0.18 - dayShift, dot(surfaceNormal, lightDir));
      float shade = mix(0.05, 1.0, lit) * night;

      float conflictBias = u_longMemory.x;
      float stabilityBias = u_longMemory.y;
      float curiosityBias = u_longMemory.z;

      float pi = 3.14159265;
      vec2 sphereUv = vec2(
        atan(surfaceNormal.z, surfaceNormal.x) / (2.0 * pi) + 0.5,
        asin(surfaceNormal.y) / pi + 0.5
      );

      vec2 seed = u_continentSeed * 2.0 - 1.0;
      float jagged = clamp(0.12 + conflictBias * 0.55, 0.08, 0.7);

      float yaw = seed.x * 6.2831;
      float pitch = seed.y * 0.6;

      vec3 base1 = normalize(vec3(1.0, 1.0, 1.0));
      vec3 base2 = normalize(vec3(-1.0, -1.0, 1.0));
      vec3 base3 = normalize(vec3(-1.0, 1.0, -1.0));
      vec3 base4 = normalize(vec3(1.0, -1.0, -1.0));

      vec3 c1 = rotateY(rotateX(base1, pitch), yaw);
      vec3 c2 = rotateY(rotateX(base2, pitch), yaw);
      vec3 c3 = rotateY(rotateX(base3, pitch), yaw);
      vec3 c4 = rotateY(rotateX(base4, pitch), yaw);

      float sizeBias = (stabilityBias - conflictBias) * 0.04;
      float r1 = mix(0.6, 0.68, hash(seed + vec2(1.2, 2.3))) - sizeBias;
      float r2 = mix(0.58, 0.66, hash(seed + vec2(3.4, 4.5))) - sizeBias * 0.9;
      float r3 = mix(0.56, 0.65, hash(seed + vec2(5.6, 6.7))) - sizeBias * 0.8;
      float r4 = mix(0.57, 0.67, hash(seed + vec2(7.8, 8.9))) - sizeBias * 0.85;

      float soft1 = mix(0.045, 0.07, hash(seed + vec2(2.1, 3.7)));
      float soft2 = mix(0.045, 0.07, hash(seed + vec2(4.2, 5.3)));
      float soft3 = mix(0.045, 0.07, hash(seed + vec2(6.1, 7.4)));
      float soft4 = mix(0.045, 0.07, hash(seed + vec2(8.5, 9.2)));

      float landMask1 = continentMask(surfaceNormal, c1, seed + vec2(1.1, 2.2), r1, soft1, jagged * 0.85);
      float landMask2 = continentMask(surfaceNormal, c2, seed + vec2(3.3, 4.4), r2, soft2, jagged * 0.95);
      float landMask3 = continentMask(surfaceNormal, c3, seed + vec2(5.5, 6.6), r3, soft3, jagged * 1.05);
      float landMask4 = continentMask(surfaceNormal, c4, seed + vec2(7.7, 8.8), r4, soft4, jagged * 0.9);

      float landMask = max(max(landMask1, landMask2), max(landMask3, landMask4));
      float land = smoothstep(0.5, 0.62, landMask);

      vec3 ocean = u_baseColor * 0.85;
      vec3 landBase = mix(u_baseColor * 0.7, u_accentColor, 0.55 + u_curiosity * 0.2);
      vec3 landColor1 = landBase * vec3(0.9, 1.05, 1.0);
      vec3 landColor2 = landBase * vec3(1.05, 0.95, 0.75);
      vec3 landColor3 = landBase * vec3(0.85, 1.0, 0.85);
      vec3 landColor4 = landBase * vec3(0.9, 0.98, 1.05);
      float landSum = landMask1 + landMask2 + landMask3 + landMask4 + 0.0001;
      vec3 landColor =
        (landColor1 * landMask1 + landColor2 * landMask2 + landColor3 * landMask3 + landColor4 * landMask4)
        / landSum;
      float coast = smoothstep(0.45, 0.52, landMask) - smoothstep(0.52, 0.6, landMask);
      vec3 coastColor = mix(u_accentColor, vec3(0.9, 0.95, 1.0), 0.25);
      vec3 surface = mix(ocean, landColor, land);
      surface = mix(surface, coastColor, coast * 0.7);

      vec2 surfUv = sphereUv * (2.4 + u_entropy * 0.6) + seed * 0.25;
      float rough = fbm(surfUv * 2.2 + vec2(1.3, -0.7));
      float ridge = ridged(surfUv * 2.8 + vec2(-0.2, 0.4));
      float reliefNoise = fbm(sphereUv * 1.6 + u_continentSeed * 3.0);
      float reliefAmp = clamp(0.02 + conflictBias * 0.06 + (1.0 - stabilityBias) * 0.03, 0.02, 0.12);
      float relief = (reliefNoise - 0.5) * reliefAmp;

      float terrain = 0.92 + rough * 0.12 + ridge * 0.06 + relief * land;
      surface *= mix(1.0, terrain, land * 0.75);

      float epochScaleA = mix(1.2, 2.4, u_epochA.z);
      float epochScaleB = mix(1.1, 2.1, u_epochB.z);
      float epochNoiseA = fbm(sphereUv * epochScaleA + u_epochSeedA * 2.2);
      float epochNoiseB = fbm(sphereUv * epochScaleB + u_epochSeedB * 2.2);
      float epochLayerA = smoothstep(0.5, 0.75, epochNoiseA) * u_epochA.w;
      float epochLayerB = smoothstep(0.45, 0.7, epochNoiseB) * u_epochB.w;
      vec3 epochTintA = epochColor(u_epochA.xyz);
      vec3 epochTintB = epochColor(u_epochB.xyz);
      surface += epochTintA * epochLayerA * 0.12 * (0.4 + land * 0.6);
      surface += epochTintB * epochLayerB * 0.08 * (0.4 + land * 0.6);

      float floraNoise = fbm(sphereUv * 7.5 + u_continentSeed * 6.0);
      float floraMask = smoothstep(0.55, 0.75, floraNoise) * flora * land;
      surface += vec3(0.06, 0.14, 0.08) * floraMask * 1.2;

      float lat = surfaceNormal.y;
      float seasonal = sin(u_time * 0.003 + u_midMemory.y * 2.0);
      float bandFreq = mix(1.6, 4.2, u_midMemory.z) + seasonal * 0.25;
      float bandPhase = u_continentSeed.x * 6.2831 + u_time * 0.004;
      float drift = sin(u_time * 0.0015 + u_continentSeed.y * 5.0) * 0.15;
      float bandWave = 0.5 + 0.5 * sin((lat + drift) * bandFreq + bandPhase + u_time * 0.015);
      float bandSharp = mix(0.16, 0.42, u_midMemory.x);
      float band = smoothstep(0.5 - bandSharp, 0.5 + bandSharp, bandWave);
      float bandStrength = mix(0.1, 0.35, 1.0 - u_midMemory.y) * (0.85 + seasonal * 0.15);
      float sent = clamp(u_midMemory.w, -1.0, 1.0);
      vec3 bandCool = vec3(0.08, 0.25, 0.42);
      vec3 bandWarm = vec3(0.35, 0.18, 0.2);
      vec3 bandColor = mix(bandCool, bandWarm, clamp(-sent, 0.0, 1.0));
      bandColor = mix(bandColor, vec3(0.2, 0.55, 0.7), u_midMemory.z);
      surface += bandColor * band * bandStrength * (0.35 + u_midMemory.z * 0.2) * (1.0 - land);

      vec2 cloudUv = cloudNormal.xy * (4.6 + u_entropy * 2.8);
      float cloudNoise = fbm(cloudUv + u_time * (0.06 + u_curiosity * 0.16 + storm * 0.08));
      float clouds = smoothstep(0.6, 0.82, cloudNoise) * (0.2 + u_trust * 0.45 + storm * 0.45);
      surface = mix(surface, vec3(0.85), clouds * (0.28 + storm * 0.25));

      surface *= shade;
      surface = mix(surface, surface * 0.58, u_fear);
      surface = mix(surface, surface * 0.85, storm * 0.6);

      vec3 reflectDir = reflect(-lightDir, surfaceNormal);
      float spec = pow(max(dot(reflectDir, viewDir), 0.0), 36.0 + u_trust * 40.0);
      surface += spec * (0.06 + u_trust * 0.12);

      float techNoise = fbm(surfaceNormal.xy * 8.0 + vec2(t * 2.5, -t * 1.8));
      float techLines = smoothstep(0.82, 0.94, techNoise) * (0.2 + u_tension * 0.5);
      float nightGlow = (1.0 - night) * land * techLines;
      surface += u_accentColor * nightGlow * 0.5;

      float rain = smoothstep(0.7, 0.95, fbm(vec2(sphereUv.x * 60.0, u_time * (1.2 + storm))));
      float rainMask = rain * storm * (1.0 - land) * 0.35;
      surface = mix(surface, surface * vec3(0.7, 0.75, 0.8), rainMask);

      color = mix(color, surface, planetMask);

      float rim = pow(1.0 - max(dot(surfaceNormal, viewDir), 0.0), 2.8);
      float atmo = smoothstep(edge + 0.11 + u_trust * 0.08, edge, r);
      vec3 glow = u_accentColor * (0.22 + u_trust * 0.55 + flora * 0.15) * atmo * rim;
      color += glow * (1.0 + u_cinematic * 0.45);

      float ring = smoothstep(edge + 0.13, edge + 0.065, r);
      ring *= smoothstep(edge + 0.02, edge + 0.08, r);
      float ringNoise = fbm(uv * 8.0 + vec2(t * 2.0, -t * 1.2));
      ring *= 0.6 + ringNoise * 0.5;
      vec3 ringColor = mix(vec3(0.15, 0.7, 1.0), u_accentColor, 0.55);
      color += ringColor * ring * (0.22 + u_curiosity * 0.35);

      float epochRingA = smoothstep(edge + 0.2, edge + 0.14, r);
      epochRingA *= smoothstep(edge + 0.08, edge + 0.13, r);
      float epochRingB = smoothstep(edge + 0.26, edge + 0.2, r);
      epochRingB *= smoothstep(edge + 0.14, edge + 0.19, r);
      float epochNoise = 0.7 + fbm(uv * 6.0 + vec2(t * 1.4, -t * 0.9)) * 0.6;

      vec3 epochColorA = epochColor(u_epochA.xyz);
      vec3 epochColorB = epochColor(u_epochB.xyz);
      color += epochColorA * epochRingA * epochNoise * u_epochA.w * 0.45;
      color += epochColorB * epochRingB * epochNoise * u_epochB.w * 0.3;
    }

    float vignette = smoothstep(1.2, 0.4, r);
    float cinematicVignette = mix(0.55, 0.38, u_cinematic);
    color *= mix(cinematicVignette, 1.0, vignette);

    float tone = mix(0.78, 0.6, u_cinematic);
    color = color / (color + vec3(tone));

    float grain = (hash(uv * u_resolution + u_time * 12.0) - 0.5) * (0.02 + u_cinematic * 0.03);
    color += grain;

    gl_FragColor = vec4(color, 1.0);
  }
`;

const MOOD_PALETTES = {
  calm: { base: [0.12, 0.35, 0.5], accent: [0.35, 0.8, 1.0] },
  observing: { base: [0.1, 0.3, 0.5], accent: [0.3, 0.65, 0.95] },
  curious: { base: [0.12, 0.45, 0.4], accent: [0.5, 0.95, 0.75] },
  disturbed: { base: [0.55, 0.33, 0.14], accent: [0.95, 0.7, 0.22] },
  hostile: { base: [0.55, 0.12, 0.2], accent: [0.95, 0.28, 0.42] },
};

export function createRenderer(canvas) {
  const gl = canvas.getContext("webgl", { antialias: true });
  if (!gl) return null;

  const program = createProgram(gl, VERTEX_SHADER, FRAGMENT_SHADER);
  if (!program) return null;

  gl.useProgram(program);

  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([
      -1, -1,
      1, -1,
      -1, 1,
      1, 1,
    ]),
    gl.STATIC_DRAW
  );

  const posLoc = gl.getAttribLocation(program, "a_pos");
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

  const uniforms = {
    resolution: gl.getUniformLocation(program, "u_resolution"),
    time: gl.getUniformLocation(program, "u_time"),
    tension: gl.getUniformLocation(program, "u_tension"),
    entropy: gl.getUniformLocation(program, "u_entropy"),
    curiosity: gl.getUniformLocation(program, "u_curiosity"),
    trust: gl.getUniformLocation(program, "u_trust"),
    fear: gl.getUniformLocation(program, "u_fear"),
    stability: gl.getUniformLocation(program, "u_stability"),
    baseColor: gl.getUniformLocation(program, "u_baseColor"),
    accentColor: gl.getUniformLocation(program, "u_accentColor"),
    cinematic: gl.getUniformLocation(program, "u_cinematic"),
    longMemory: gl.getUniformLocation(program, "u_longMemory"),
    continentSeed: gl.getUniformLocation(program, "u_continentSeed"),
    midMemory: gl.getUniformLocation(program, "u_midMemory"),
    epochA: gl.getUniformLocation(program, "u_epochA"),
    epochB: gl.getUniformLocation(program, "u_epochB"),
    epochSeedA: gl.getUniformLocation(program, "u_epochSeedA"),
    epochSeedB: gl.getUniformLocation(program, "u_epochSeedB"),
    daily: gl.getUniformLocation(program, "u_daily"),
  };

  let cinematic = true;

  return {
    resize(width, height) {
      gl.viewport(0, 0, width, height);
    },
    setCinematic(value) {
      cinematic = Boolean(value);
    },
    isCinematic() {
      return cinematic;
    },
    render(state, time) {
      if (!state) return;

      const presence = state.presence || {};
      const innerState = state.innerState || {};
      const longMemory = state.longMemory || {};
      const geography = state.geography || {};
      const midMemory = state.midMemory || {};
      const daily = state.daily || {};
      const identity = state.identity || {};
      const epochs = Array.isArray(state.epochs) ? state.epochs : [];

      const mood = presence.mood || "observing";
      const palette = MOOD_PALETTES[mood] || MOOD_PALETTES.observing;
      const fear = clamp(innerState.fear ?? 0.2, 0, 1);
      const trust = clamp(innerState.trust ?? 0.5, 0, 1);

      const base = mixColor(palette.base, [0.06, 0.06, 0.08], fear * 0.35);
      const accent = mixColor(palette.accent, [1, 1, 1], trust * 0.2);
      const paletteBias = clamp(identity.paletteBias ?? 0, -1, 1);
      const biasVec = [
        0.04 * paletteBias,
        -0.015 * paletteBias,
        0.05 * paletteBias,
      ];
      const baseTint = clampColor([base[0] + biasVec[0], base[1] + biasVec[1], base[2] + biasVec[2]]);
      const accentTint = clampColor([
        accent[0] + biasVec[0] * 0.8,
        accent[1] + biasVec[1] * 0.6,
        accent[2] + biasVec[2] * 0.9,
      ]);

      gl.useProgram(program);
      gl.uniform2f(uniforms.resolution, gl.canvas.width, gl.canvas.height);
      gl.uniform1f(uniforms.time, time);
      gl.uniform1f(uniforms.tension, clamp(presence.tension ?? 0.05, 0, 1));
      gl.uniform1f(uniforms.entropy, clamp(presence.entropy ?? 0.03, 0, 1));
      gl.uniform1f(uniforms.curiosity, clamp(presence.curiosity ?? 0.3, 0, 1));
      gl.uniform1f(uniforms.trust, trust);
      gl.uniform1f(uniforms.fear, fear);
      gl.uniform1f(uniforms.stability, clamp(innerState.stability ?? 0.5, 0, 1));
      gl.uniform1f(uniforms.cinematic, cinematic ? 1 : 0);
      gl.uniform3f(
        uniforms.longMemory,
        clamp(longMemory.conflict ?? 0.35, 0, 1),
        clamp(longMemory.stability ?? 0.5, 0, 1),
        clamp(longMemory.curiosity ?? 0.4, 0, 1)
      );
      gl.uniform2f(
        uniforms.continentSeed,
        clamp(geography.seedA ?? 0.37, 0, 1),
        clamp(geography.seedB ?? 0.61, 0, 1)
      );
      gl.uniform4f(
        uniforms.midMemory,
        clamp(midMemory.conflict ?? 0.4, 0, 1),
        clamp(midMemory.stability ?? 0.5, 0, 1),
        clamp(midMemory.curiosity ?? 0.4, 0, 1),
        clamp(midMemory.sentiment ?? 0.0, -1, 1)
      );

      const now = Date.now();
      const epochA = epochs[epochs.length - 1];
      const epochB = epochs[epochs.length - 2];
      const epochVecA = epochToVec(epochA, now, 1);
      const epochVecB = epochToVec(epochB, now, 0.6);
      gl.uniform4f(uniforms.epochA, epochVecA[0], epochVecA[1], epochVecA[2], epochVecA[3]);
      gl.uniform4f(uniforms.epochB, epochVecB[0], epochVecB[1], epochVecB[2], epochVecB[3]);
      const epochSeedA = epochSeedToVec(epochA, geography);
      const epochSeedB = epochSeedToVec(epochB, geography);
      gl.uniform2f(uniforms.epochSeedA, epochSeedA[0], epochSeedA[1]);
      gl.uniform2f(uniforms.epochSeedB, epochSeedB[0], epochSeedB[1]);
      gl.uniform3f(
        uniforms.daily,
        clamp(daily.trend ?? 0, -1, 1),
        clamp(daily.imprint ?? 0, -1, 1),
        clamp(daily.lastIntensity ?? 0, 0, 1)
      );
      gl.uniform3f(uniforms.baseColor, baseTint[0], baseTint[1], baseTint[2]);
      gl.uniform3f(uniforms.accentColor, accentTint[0], accentTint[1], accentTint[2]);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    },
  };
}

function createProgram(gl, vertexSrc, fragmentSrc) {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, vertexSrc);
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, fragmentSrc);
  if (!vertex || !fragment) return null;

  const program = gl.createProgram();
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error("WebGL program link failed:", gl.getProgramInfoLog(program));
    gl.deleteProgram(program);
    return null;
  }

  return program;
}

function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error("WebGL shader compile failed:", gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }

  return shader;
}

function mixColor(a, b, t) {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

function clampColor(color) {
  return [
    clamp(color[0], 0, 1),
    clamp(color[1], 0, 1),
    clamp(color[2], 0, 1),
  ];
}

function epochToVec(epoch, now, scale) {
  if (!epoch) return [0, 0, 0, 0];

  const ageDays = typeof epoch.createdAt === "number"
    ? (now - epoch.createdAt) / 86400000
    : 0;
  const ageFactor = clamp(1 - ageDays / 30, 0.2, 1);
  const strength = clamp(ageFactor * scale, 0, 1);

  return [
    clamp(epoch.conflict ?? 0, 0, 1),
    clamp(epoch.stability ?? 0, 0, 1),
    clamp(epoch.curiosity ?? 0, 0, 1),
    strength,
  ];
}

function epochSeedToVec(epoch, geography) {
  const fallbackA = clamp(geography?.seedA ?? 0.37, 0, 1);
  const fallbackB = clamp(geography?.seedB ?? 0.61, 0, 1);
  if (!epoch) return [fallbackA, fallbackB];
  return [
    clamp(epoch.seedA ?? fallbackA, 0, 1),
    clamp(epoch.seedB ?? fallbackB, 0, 1),
  ];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
