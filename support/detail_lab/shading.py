"""Preserve material colour in emissive previews; no coloured-light simulation."""
LEGACY_EMISSION='if(vEmission>.5)c=mix(vec3(.87,.96,.83),vec3(.84,1.,.83),uNight);'
MATERIAL_EMISSION='if(vEmission>.5)c=vColor;'

def emission_shader(source, policy='material'):
    if policy not in {'material','legacy'}:
        raise ValueError('unknown emission policy')
    if policy=='legacy':return source
    if LEGACY_EMISSION not in source:
        raise ValueError('Unrecognised shader: review emissive colour handling')
    return source.replace(LEGACY_EMISSION,MATERIAL_EMISSION)
