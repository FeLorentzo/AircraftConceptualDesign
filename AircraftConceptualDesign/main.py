import numpy as np
from ambiance import Atmosphere
import json
import matplotlib.pyplot as plt
import aircraftconceptualdesign as acd
import units

# Initial requirements based on cargo mission stablished. The project velocity is based on cruise mission

aircraft = {
    'definitions': {
        'MTOW': units.lbm2kg(19000),  # Kg, assuming MTOW given by FAR23
        'V_cruise': units.knot2ms(230),  # m/s, assuming CAS
        'W_empty/W': 0.6,  # from database
        'W_crew': 200,  # 2 pilots
        'operational ceiling': units.ft2m(25000),
    },
    'engine': {
        'power': units.hp2Watt(1600)
    },
    'wing': {},
    'ht': {},
    'vt': {},
    'fus': {},
    'landing gear': {},
}

# Atmosphere objects

isa_ceiling = Atmosphere(aircraft['definitions']['operational ceiling'])
isa_sealevel = Atmosphere(0)

# Compute range based on MTOW from database
range = 0.0854*aircraft["MTOW"] + 461
print(f'Range previewed by database: {range} nm')  # ~ 1100 nm


g = 9.81
rho_SL = isa_sealevel.density[0]  # Air density sea level

# Mission profile
missao = {
    "Perfil": ['Take off', 'Ascending', 'Cruise_1', 'Descending', 'Loitter', 'Cruise_2', 'Landing'],
    "Range_1": units.mi2m(range),
    "Range_2": units.mi2m(100),
    "Loitter_time": 20 * 60
}

aircraft['missao'] = missao


## Calculations on initial performance ##

# Empty weight
aircraft["W_empty"] = aircraft["W_empty/W"] * aircraft["MTOW"]
print(f'Empty weight: {aircraft["W_empty"]}')

# wing load estimation, through data linearization of database. 
# is given by Kg of MTOW/ wing area; must be converted in N

aircraft["wing_load"] = (0.00846 * aircraft["MTOW"] + 121)*g
print(f'Wing load: {aircraft["wing_load"]:.0f}')

# Designing wing area for cruise condition, assuming 5% of fuel consumption
aircraft['wing']["S"] = 0.95*aircraft["MTOW"] * g / aircraft["wing_load"]
print(f'Wing area: {aircraft["wing"]["S"]:.1f}')

# Defining Cl for cruise condition
aircraft["Cl cruise"] = aircraft["wing_load"] / \
    (0.5 * rho_SL * (aircraft["V_cruise"]**2))
print(f'Cruise sea level Cl: {aircraft["Cl cruise"]:.2f}')

# Estimate required thrust. Assuming, in cruise, 65% of maximum power;
# proppeler efficiency of 80%; sea level
power_cruise = 0.65 * aircraft["engine"]["power"]
eta = 0.65

aircraft['engine']["thrust cruise"] = eta * power_cruise / aircraft["V_cruise"]
aircraft["Thrust_to_weight"] = aircraft["engine"]["thrust cruise"] / \
    (aircraft["MTOW"]*g)
print(f'Empuxo do motor: {aircraft["engine"]["thrust cruise"]:.2f}')

aircraft["Cd cruise"] = aircraft["engine"]["thrust cruise"] / \
    (0.5 * rho_SL * (aircraft["V_cruise"]**2) * aircraft["wing"]["S"])
print(f'Cd de cruzeiro a nível do mar: {aircraft["Cd cruise"]:.4f}')
print(
    f'L/D de cruzeiro a nível do mar: {aircraft["Cl cruise"]/aircraft["Cd cruise"]:.2f}')

# Compute SFC cruise and loiter through Raymer method
aircraft["engine"]['SFC_cruise'] = 0.5 * \
    aircraft['V_cruise'] / (units.hp2Watt(550) * 0.8)
aircraft["engine"]['SFC_loiter'] = 0.6 * \
    aircraft['V_cruise'] / (units.hp2Watt(550) * 0.8)
print(f'Consumo cruise : {aircraft["engine"]["SFC_cruise"]:e}')
print(f'Consumo loiter : {aircraft["engine"]["SFC_loiter"]:e}')

# Compute stall
aircraft['V_stall'] = np.sqrt(
    2*aircraft["MTOW"]*g/(rho_SL * aircraft['wing']['S'] * 2))
print(f"Vel. Stall : {aircraft['V_stall']}")


## First weight estimative ##

wf_frac = 1 - acd.first_weight_estimate(aircraft)

print(wf_frac)

print(f'wf/w0= {wf_frac}')
print(f'wf = {wf_frac*aircraft["definitions"]["MTOW"]}')
print(f'vol = {wf_frac*aircraft["definitions"]["MTOW"]/0.72}')

w_pay = aircraft["definitions"]['MTOW'] * \
    (1 - wf_frac - aircraft["definitions"]
     ['W_empty/W']) - aircraft["definitions"]['W_crew']
print(f'Payload: {w_pay}')


## Estimating areas of tail, flap and aileron ##

print(f"S_ref: {aircraft['wing']['S']:.3f}")

aircraft = acd.estimate_aerodynamic_areas(aircraft)

print(f"""S_ref: {aircraft['wing']['S']:.3f}
S_Ht: {aircraft['ht']['S']:.3f}
S_profundor: {aircraft['ht']['S_elevator']:.3f}
S_Vt: {aircraft['vt']['S']:.3f}
S_leme: {aircraft['vt']['S_rudder']:.3f}
S_flap: {aircraft['wing']['S_flap']:.3f}
S_aileron: {aircraft['wing']['S_aileron']:.3f}
""")

## Including wet areas estimatives from CAD of the aircraft ##

aircraft['wing']['S_wet'] = 84.4
aircraft['ht']['S_wet'] = 18.4
aircraft['vt']['S_wet'] = 12.3
aircraft['fus']['S_wet'] = 95.4

## Updating parameters from CAD of the aircraft ##

wing_param = {
    'b': 21,
    'CMA': 1.965,
    'S_wet': 84.4,
    'Percent_laminar': 0.1,
    'thickness': 0.1,  # provisory
    # must be compatible with weight_estimation_data.json file
    'material': "Aerospace aluminum",
}

ht_param = {
    'b': 6.5,
    'CMA': 1.491,
    'S_wet': 18.4,
    'Percent_laminar': 0.1,
    'thickness': 0.1,  # provisório
    # must be compatible with weight_estimation_data.json file
    'material': "Aerospace aluminum",
}

vt_param = {
    'b': 2.75,
    'CMA': 2.156,
    'S_wet': 12.3,
    'Percent_laminar': 0.1,
    'thickness': 0.1,  # provisório
    # must be compatible with weight_estimation_data.json file
    'material': "Aerospace aluminum",
}

fus_param = {
    'length': 18,
    'S_wet': 95.9,
    'diameter': 1.6,
    'Percent_laminar': 0,
    # must be compatible with weight_estimation_data.json file
    'material': "Aerospace aluminum",
}

aircraft['wing'].update(wing_param)
aircraft['ht'].update(ht_param)
aircraft['vt'].update(vt_param)
aircraft['fus'].update(fus_param)


## Drag estimative ##

# Friction drag

Cf = 0
isa = Atmosphere(aircraft['definitions']['operational ceiling'])
rho = isa.density[0]
T = isa.temperature[0]
mu = isa.dynamic_viscosity[0]
vel_som = isa.speed_of_sound[0]
Mach = aircraft['definitions']['V_cruise']/vel_som
Re_operational = rho * \
    aircraft['definitions']['V_cruise'] * aircraft['wing']['CMA'] / mu

print(f'Operational Reynolds = {Re_operational:.3e}')
print(f'Operational Mach = {Mach:.3f}')

print(20*'-')

for key, component in aircraft.items():
    if key == 'fus':
        cut = acd.Re_cutoff(component['length'])
        Re = rho * aircraft['definitions']['V_cruise'] * \
            component['length'] / mu
    elif 'CMA' in component:
        cut = acd.Re_cutoff(component['CMA'])
        Re = rho * aircraft['definitions']['V_cruise'] * component['CMA'] / mu
    else:
        continue

    print(f'Reynolds cutoff: {cut:.2e}')
    print(f'Reynolds: {Re:.2e}')

    if Re > cut:
        Re = cut

    component['Cf'] = component['Percent_laminar'] * acd.Cf_laminar(cut) + (
        1-component['Percent_laminar']) * acd.Cf_turbulent(cut, Mach)
    print(f'Cf do {key}: {component["Cf"]:.4f}\n')

# Form Factor drag

M = aircraft['definitions']['V_cruise']/vel_som

aircraft = acd.compute_FF(aircraft, M)

print(f"""
Wing form factor: {aircraft["wing"]["FF"]:.4f}
Horizontal stabilizer form factor:  {aircraft["ht"]["FF"]:.4f}
Vertical stabilizer form factor: {aircraft["vt"]["FF"]:.4f} 
Fuselage form factor: {aircraft["fus"]["FF"]:.4f}
""")

# Interference drag

aircraft['wing']['Q_int'] = 1
aircraft['ht']['Q_int'] = 1.05
aircraft['vt']['Q_int'] = 1.05
aircraft['fus']['Q_int'] = 1

# Miscelaneos drag due fuselage upsweep

mu = np.arctan(631/8656)
Amax = np.pi*0.8**2

Cd_misc = 3.83*mu**2.5*Amax / aircraft['wing']['S']

print(f'Cd de miscelânia = {Cd_misc:.4f}')

# Compute total parasite drag

Cd_p = 0

for component, values in aircraft.items():
    if 'Cf' in values:
        Cd_c = values["Cf"]*values['FF']*values['Q_int'] * \
            values['S_wet'] / aircraft["wing"]["S"]
        print(
            f'Componente de arrasto parasita em {component} vale = {Cd_c:.4f}\n')
        Cd_p += Cd_c

print(f'Arrasto parasita total sem componente de miscelânia = {Cd_p:.4f}\n')

Cd_p += Cd_misc

print(f'Arrasto parasita total com componente de miscelânia = {Cd_p:.4f}\n')


## Drag x velocity curves ##

# Parasite drag

vector_v = np.linspace(15, 1.4 * aircraft['definitions']['V_cruise'], 80)

rho_SL = isa_sealevel.density[0]

D_p = 0.5 * rho_SL * vector_v ** 2 * aircraft['wing']['S'] * Cd_p

# Induced drag

AR = aircraft['wing']['b']**2 / aircraft['wing']['S']
e = acd.compute_oswald(AR)
W = aircraft['definitions']['MTOW']
S = aircraft['wing']['S']

CL_for_Cdi_induced = 2 * W * g / (rho_SL * vector_v ** 2 * S)

K = 1 / (np.pi * AR * e)

Cd_i = K * CL_for_Cdi_induced ** 2

D_i = 0.5 * rho_SL * vector_v ** 2 * aircraft['wing']['S'] * Cd_i

print(f'Alongamento = {AR:.2f}')
print(f'Coeficiente de Oswald = {e:.2f}')
print(f'Fator k = {K:.4f}')
print(f'CDi = {Cd_i}')

# Plot

plt.figure()
plt.plot(vector_v, D_p, 'b', label='Parasite drag')
plt.plot(vector_v, D_i, 'r', label='Induced drag')
plt.plot(vector_v, D_p + D_i, 'g', label='Total drag')
plt.xlabel('Velocity CAS [m/s]')
plt.ylabel('Drag [N]')
plt.grid()
plt.legend()


# Constraint analysis
