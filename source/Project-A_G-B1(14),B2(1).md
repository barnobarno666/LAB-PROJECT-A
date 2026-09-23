# Mechanistic Modeling, Simulation, and Optimization of a Fixed-Bed Ni/Al₂O₃ Reactor for CO Methanation

**A ChE-402 project report**  
**Course:** ChE-402: Chemical Engineering Laboratory-V  
**Academic Session:** L-4 T-1  
**Lab Groups:** B1-14, B2-1  

---

### Submitted by:

| Group B1-14 | Group B2-1 |
| :--- | :--- |
| **Mehrab Bin Sohrab** (2102063) | **Subarno Sadat Barno** (2102091) |
| **Effat Ara Ouishi** (2102064) | **Zannatul Ferdous Khan** (2102092) |
| **Mahbuba Rahman Rimi** (2102077) | **Sidratul Muntaha Subah** (2102093) |
| **Abdullah Al Hussain** (2102079) | **Ashiqul Habib Amit** (2102094) |
| **Md. Shihab Hossain** (2102080) | **Rifat Hossain** (2102095) |

---

### Submitted to:
**Md. Farhatul Abrar**  
Lecturer  
Department of Chemical Engineering, BUET  

**Date of Submission:** 22.08.2026  

<p align="center">
  <img src="buet_logo.png" alt="BUET Logo" width="160"/>
</p>

<p align="center">
  <strong>DEPARTMENT OF CHEMICAL ENGINEERING</strong><br/>
  <strong>BANGLADESH UNIVERSITY OF ENGINEERING AND TECHNOLOGY</strong>
</p>

---

## Statement of Academic Integrity

The authors hereby attest that this report is an original work completed for the course ChE-402. Various academic and online resources, including research papers, review articles, textbooks, and other publicly available materials, were consulted during the preparation of this report. Artificial intelligence tools and Grammarly were also used for language refinement, grammar checking, and improving clarity of expression. However, the core ideas, analysis, calculations, interpretations and overall preparation of the report were carried out by the authors. All external sources used in the report have been acknowledged and cited where appropriate.

### Authors:
- 2102063 - Mehrab Bin Sohrab
- 2102064 - Effat-Ara Ouishi
- 2102077 - Mahbuba Rahman Rimi
- 2102079 - Abdullah Al Hussain
- 2102080 - Md. Shihab Hossain
- 2102091 - Subarno Sadat Barno
- 2102092 - Zannatul Ferdous Khan 
- 2102093 - Sidratul Muntaha Subah
- 2102094 - Ashiqul Habib Amit
- 2102095 - Rifat Hossain

---

## Acknowledgments

The authors would like to express their sincere gratitude to Farhatul Abrar Sir, Lecturer of Department of Chemical Engineering, BUET, for his continuous guidance, valuable suggestions and generous support throughout this project. His insightful feedback, technical advice and encouragement greatly helped us improve our understanding, correct our work and complete the project in a more organized and effective manner.

We are especially thankful for the time and effort he dedicated to reviewing our progress and helping us overcome difficulties encountered during the project. His guidance played an important role in the successful completion of this work.

---

## Abstract

This project focuses on the mechanistic modeling, simulation and optimization of a fixed-bed Ni/Al₂O₃ reactor for CO methanation. The reaction system considers CO methanation together with relevant side reactions such as the water-gas shift reaction and CO₂ methanation to explain the experimentally observed product distribution. A one-dimensional plug-flow reactor model incorporating reaction kinetics, species balances, and energy balance is developed to predict conversion, selectivity, and temperature profiles along the reactor bed. The model is validated using experimental GC data and then used to investigate the effects of operating variables such as temperature, pressure, H₂/CO ratio, flow rate and catalyst loading. Finally, the model is applied to identify operating conditions that improve CO conversion and CH₄ selectivity while limiting CO₂ formation and excessive temperature rise.

---

## Background

### CO Methanation and Reaction Network

Catalytic methanation is an established route for converting carbon oxides and hydrogen into methane. In the present system, carbon monoxide methanation is the principal reaction and proceeds over a supported nickel catalyst according to:

$$\text{CO} + 3\text{H}_2 \rightleftharpoons \text{CH}_4 + \text{H}_2\text{O}$$

The reaction is strongly exothermic, with a standard reaction enthalpy of approximately $-206.1\text{ kJ mol}^{-1}$. It also decreases the total number of gas-phase moles from four to two. Consequently, equilibrium methane formation is favored by lower temperature and higher pressure, whereas the intrinsic reaction rate generally benefits from increasing temperature. This creates a fundamental design compromise: sufficiently high temperature is required to obtain useful kinetics, but excessive temperature can reduce equilibrium methane yield, intensify hot-spot formation, accelerate catalyst sintering, and promote undesirable side chemistry [4,6,13].

The project cannot be represented adequately by the primary methanation reaction alone because CO₂ was experimentally detected in the reactor products. The most direct mechanistic explanation is the water-gas shift (WGS) reaction. Water produced by methanation can react with residual CO to form CO₂ and H₂:

$$\text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2$$

Mo et al. identified WGS as a plausible side reaction during CO methanation, while the broader COₓ kinetic literature supports treating the WGS/RWGS pair as a reversible reaction that couples the CO and CO₂ networks [6,7,12]. Thus, even when CO₂ is absent or negligible in the inlet, it can be generated progressively along the catalytic bed as H₂O accumulates. Once formed, CO₂ may also undergo methanation:

$$\text{CO}_2 + 4\text{H}_2 \rightleftharpoons \text{CH}_4 + 2\text{H}_2\text{O}$$

A second possible source of CO₂ is the Boudouard or CO disproportionation reaction:

$$2\text{CO} \rightleftharpoons \text{CO}_2 + \text{C}$$

This pathway is important because it simultaneously forms CO₂ and deposits solid carbon. However, the literature indicates that it should not automatically be assumed to dominate the observed CO₂ formation. In the absence of direct evidence of carbon deposition, a poor carbon balance, or pronounced deactivation under hydrogen-deficient conditions, reversible WGS remains the more defensible first explanation [6,7]. Therefore, a realistic minimum reaction network for the present reactor consists of CO methanation and reversible WGS, with CO₂ methanation included because CO₂ formed inside the bed can subsequently compete for hydrogen and surface sites. Carbon formation can then be incorporated if experimental evidence justifies it [7,12].

### Ni/Al₂O₃ Catalyst: Active Phase, Dispersion, and Metal-Support Interaction

Nickel is widely used for methanation because it combines relatively high catalytic activity and methane selectivity with much lower cost than noble metals. Alumina is an attractive support because it provides high surface area and can disperse nickel over the catalyst surface. Nevertheless, Ni/Al₂O₃ performance cannot be described simply by nominal nickel loading. The accessible metallic nickel surface, crystallite size, dispersion, reducibility, metal-support interaction, preparation route, calcination history, and reduction history all influence the number and nature of active sites [4-7].

The interaction between nickel and alumina is especially important because it has both beneficial and detrimental consequences. Moderate interaction can stabilize small nickel particles and reduce migration or sintering, whereas excessively strong interaction can promote formation of nickel aluminate species such as NiAl₂O₄ that are difficult to reduce and therefore decrease the population of accessible metallic nickel sites. Yu et al. demonstrated this distinction using a cold-plasma route to decompose a Ni-MOF@Al₂O₃ precursor. Their plasma-derived catalyst showed smaller nickel particles, an increase in Ni dispersion from 4.6% to 26.5%, and suppression of NiAl₂O₄ formation relative to a conventionally calcined catalyst [5]. Density-functional calculations in the same study indicated strong CO₂ adsorption at the Ni-Al₂O₃ interface and much weaker activation on NiAl₂O₄, showing that metallic Ni and an appropriate interfacial environment can both contribute to catalytic activity [5].

At the same time, strong metal-support interaction should not be treated as universally undesirable. Chang et al. reported that a high-shear-mixer-assisted coprecipitation and spray-drying route produced smaller and more uniformly dispersed Ni particles, increased pore volume, and strengthened useful metal-support interaction. The resulting catalyst showed markedly improved low-temperature methanation performance and a reduction in apparent activation energy for CO methanation from 89.03 to 76.31 kJ mol⁻¹ [4]. These observations suggest that the desired catalyst requires a balance: sufficient interaction to stabilize highly dispersed nickel, but not so much irreversible Ni-Al interaction that reducible metallic nickel becomes severely limited.

### Influence of Precursor, Preparation Route, Supports, and Promoters

Catalyst preparation strongly affects the apparent kinetic behavior of Ni-based methanation catalysts. Mo et al. investigated Ni-Al₂O₃ catalysts prepared from nickel nitrate, nickel chloride, and nickel acetate precursors. The nitrate-derived material produced well-dispersed Ni with a crystallite size of 6.80 nm and exhibited the strongest resistance to carbon deposition among the tested materials, whereas the acetate-derived catalyst gave the highest CO conversion but poorer resistance to refractory carbon formation [6]. This distinction is important for reactor design because the catalyst giving the highest initial conversion is not necessarily the catalyst that provides the best long-term stability.

Support modification can also alter nickel reducibility and the number of accessible active sites. Zhang et al. modified NiO/Al₂O₃ with MgO, ZrO₂, and SiO₂ and found that all three additives weakened unfavorable Ni-Al interaction and increased the amount of accessible nickel. Under their experimental conditions, the MgO-modified catalyst showed the strongest improvement in CO methanation performance [8]. These results demonstrate that support chemistry can change apparent activity even when the nominal active metal remains nickel.

Wang et al. provided a related example using Ni/Al₂O₃-ZrO₂ catalysts prepared at different calcination temperatures. The intermediate calcination condition produced a favorable combination of surface area, Ni dispersion, metallic Ni surface area, and crystallite size, whereas the highest calcination temperature promoted NiAl₂O₄ formation and damaged the pore structure [9]. This finding reinforces the concept that an optimum metal-support interaction and thermal history are required rather than simply maximizing or minimizing interaction strength.

Studies using other supports and promoters further show that adsorption characteristics are controlled by the chemical environment surrounding the Ni sites. Cue Gonzalez et al. reported that Ni supported on natural clay could maintain high CO₂ conversion and nearly complete CH₄ selectivity at elevated temperature, illustrating how support composition and mineral phases can contribute to catalytic behavior [2]. Usman et al. examined Ba-, La-, and Ce-promoted Ni/SiO₂-Al₂O₃ catalysts. Cerium improved low-temperature performance through smaller NiO crystallites, oxygen vacancies, appropriate basicity, and improved Ni dispersion, while barium enhanced CO₂ adsorption and produced the highest CO₂ conversion among the promoted samples under their conditions [3]. These studies are not direct sources of intrinsic CO-methanation rate constants for the project reactor, but they explain why adsorption constants and apparent activity can vary substantially from one Ni catalyst to another.

### Surface Mechanism and Kinetic Modeling

A mechanistic reactor model requires rate expressions that account for temperature, partial pressures, adsorption, thermodynamic driving force, and competition among surface species. The foundational work of Xu and Froment developed thermodynamically consistent Langmuir-Hinshelwood-type kinetic expressions for methane steam reforming, methanation, and water-gas shift over a Ni/MgAl₂O₄ catalyst [10]. Although that catalyst and operating system are not identical to the present Ni/Al₂O₃ reactor, the study established an important modeling framework in which adsorption and surface reaction steps are represented explicitly rather than embedded only in empirical reaction orders.

Subsequent work has shown that a single universal elementary mechanism cannot be assumed for all Ni catalysts. Depending on catalyst structure and reaction environment, CO₂ methanation may proceed through dissociative pathways or hydrogen-assisted routes involving surface species such as CO*, COOH*, HCOO*, or CHO*. For CO methanation on Ni/Al₂O₃, dissociative carbon pathways have received substantial support. Strongly adsorbed CO can occupy a large fraction of the nickel surface; under hydrogen-rich conditions, CO-derived intermediates can be hydrogenated toward methane, whereas high CO surface coverage can favor C* formation, nickel carbide, and coke [7].

This competitive adsorption behavior is central to selecting an appropriate kinetic model. Celoria et al. investigated CO methanation, CO₂ methanation, and mixed CO/CO₂ methanation over 24 wt% Ni/Al₂O₃. More than 300 reaction conditions generated 907 observations, of which 852 were retained for kinetic parameter regression [7]. Separate power-law models were able to describe single-feed CO or CO₂ methanation reasonably well, but they failed to reproduce the coupled behavior of co-methanation because they did not capture preferential CO adsorption and competition for common surface sites. In contrast, their three-reaction Langmuir-Hinshelwood-Hougen-Watson (LHHW) M4 model successfully represented CO₂ methanation, CO methanation, and RWGS through a common adsorption framework [7].

The M4 structure is particularly relevant to the present project because the reactor feed initially contains mainly CO and H₂, whereas the generation of CO₂ and H₂O causes the composition to evolve into a coupled CO/CO₂/H₂/H₂O/CH₄ system along the bed. Quindimil et al. independently developed intrinsic LHHW kinetics for CO₂ methanation on low-loaded Ni/Al₂O₃ and identified water inhibition together with carbonyl- and formate-related surface chemistry [11]. Langer and Freund evaluated a large set of parameterized COₓ methanation models over a broad operating range and likewise found that an adsorption-based LHHW formulation was required to account for effects associated with strongly adsorbed CO [12]. Taken together, these studies support using a mechanistic adsorption-based multi-reaction model for the final reactor simulation, while retaining simpler power-law expressions only as preliminary or narrow-range approximations.

### Transferability of Literature Kinetics to the Project Catalyst

The literature provides a strong basis for the form of the rate equations, but the numerical parameters cannot be transferred without caution. The M4 parameters of Celoria et al. were obtained for a 24 wt% Ni/Al₂O₃ catalyst tested at approximately 250-400 °C and 5 or 15 bar [7]. Other studies reviewed here employed nickel loadings ranging from only a few weight percent to much higher values, different alumina phases or composite supports, different precursors, and different calcination and reduction procedures [3-9]. Each of these factors can modify active-site density, adsorption strength, reducibility, and carbon resistance.

Consequently, the kinetic equation structure is more transferable than the fitted parameter values. Applying published pre-exponential factors, adsorption constants, or deactivation parameters directly to the project catalyst as if all Ni/Al₂O₃ materials were identical would be unjustified. A more defensible strategy is to use the literature kinetic form as the mechanistic foundation and then validate it against the project GC data. If necessary, a catalyst activity factor or a limited number of selected kinetic parameters can be fitted or scaled, provided that the fitted factor is clearly distinguished from the intrinsic literature parameters [7].

### Fixed-Bed Reactor Modeling and Thermal Behavior

For reactor-scale simulation, the reviewed literature supports treating the catalyst bed as a one-dimensional pseudo-homogeneous plug-flow system as a first approximation. Celoria et al. modeled their laboratory reactor as a one-dimensional isobaric plug-flow reactor with negligible axial dispersion and expressed species balances per unit catalyst mass [7]. For the present project, the model should track at least CO, H₂, CH₄, H₂O, and CO₂. Any inert gas used experimentally should be retained in the total molar-flow and heat-capacity calculations even though it does not participate in the reaction network.

A species-only isothermal model is insufficient for final optimization because methanation is highly exothermic. Temperature affects the kinetic constants, adsorption constants, equilibrium constants, and physical properties simultaneously. As the reaction accelerates, heat release can increase the local bed temperature, which in turn further modifies the reaction rates. This feedback can create sharp temperature and rate maxima near the reactor entrance. At sufficiently high temperature, equilibrium limitations, Ni sintering, carbon chemistry, and side reactions become increasingly important [1,13].

Pilot-scale observations provide direct evidence for the need to include heat transfer. Deiana et al. studied a monotube plug-flow methanation reactor with a Ni-based catalyst and a diathermic-oil heat-transfer circuit. Their system reached approximately 70% CO₂ conversion and a maximum CH₄ concentration of 63.4 vol%, while local temperatures in the catalytic region could rise to roughly 475-500 °C even when the heat-transfer oil was near 300 °C [1]. The reactor used thermal-management measures including separate catalytic zones and external heat removal. These observations show that furnace or coolant temperature cannot simply be assumed to equal the catalyst-bed temperature. Therefore, the project model should couple species balances with an axial energy balance and should evaluate either measured-wall-temperature, heat-transfer, or adiabatic limiting cases as appropriate.

Pressure drop should also be examined. In a packed bed, changes in pressure alter gas partial pressures and therefore affect both adsorption and equilibrium driving forces. The Ergun equation provides the standard basis for estimating this pressure loss. A constant-pressure approximation is acceptable only if the estimated or measured pressure drop is small relative to the reactor operating pressure. Transport limitations should likewise be checked so that apparent kinetic behavior is not incorrectly attributed to intrinsic surface kinetics [7].

### Catalyst Deactivation and Stability

Catalyst deactivation is an important extension of the steady-state reaction model. The literature identifies several mechanisms relevant to Ni/Al₂O₃, including sintering, coking, nickel-carbide formation, oxidation, poisoning, and formation of difficult-to-reduce Ni-Al species. High temperature promotes particle growth and loss of metallic surface area, while high CO surface coverage and hydrogen-deficient feeds increase the tendency toward carbon formation [6,7].

Celoria et al. observed different stability behavior for CO and CO₂ methanation. CO₂ methanation produced comparatively mild sintering, whereas CO methanation showed stronger deactivation associated with carbon-rich surface species, nickel carbide, and carbon deposition. At the stoichiometric H₂/CO ratio of 3, carbon deposition contributed to a noticeable loss of activity, while increasing the hydrogen ratio above stoichiometric improved stability [7]. Their study also showed that O₂ can reduce stability through reoxidation, C₂H₄ promotes coking, and H₂S causes essentially irreversible poisoning of Ni sites [7]. Mo et al. independently showed that smaller, better-dispersed Ni can improve resistance to carbon deposition [6].

For the current project, deactivation does not need to be included in the first steady-state model unless the experimental dataset contains sufficient time-on-stream information to identify it reliably. A logical progression is to establish the intrinsic reaction network and thermal model first, validate the steady-state outlet composition, and then introduce a catalyst activity factor. A time-dependent deactivation expression should be added only if the available data can distinguish true catalyst deactivation from measurement scatter or thermal stabilization [7].

### Effects of Operating Conditions

Temperature, pressure, feed composition, residence time, gas hourly space velocity (GHSV), catalyst loading, heat-transfer conditions, and catalyst activity all influence methanation performance. Their effects are coupled through intrinsic kinetics, adsorption, equilibrium, and transport. Increasing pressure generally favors methane formation thermodynamically because the methanation reactions reduce the number of gas-phase moles. However, the actual kinetic response also depends on surface coverage and the specific adsorption model [1,7].

Residence time and catalyst loading affect conversion in complementary ways. Increasing flow rate at fixed catalyst mass reduces residence time and normally decreases the extent of reaction, while increasing catalyst mass at fixed flow increases available catalytic capacity. Because the reaction is exothermic, however, increased conversion can also intensify the temperature rise, so conversion and hot-spot formation must be evaluated together rather than independently [1,13].

The H₂/CO ratio is especially significant because it controls both methanation stoichiometry and carbon-formation tendency. The stoichiometric ratio for CO methanation is 3, and hydrogen-deficient conditions favor carbon-rich surface species and coking. The reviewed deactivation studies indicate that a modest excess of hydrogen can improve stability, although the optimum ratio for the project reactor must be determined from the coupled kinetic and thermal model rather than transferred directly from another catalyst system [7]. These variables therefore provide the natural basis for sensitivity analysis and subsequent optimization.

### Implications for Model Development and Validation

The combined literature suggests a staged modeling strategy for the present fixed-bed reactor. The first step is to define a thermodynamically consistent reaction network and calculate the temperature dependence of equilibrium behavior for CO methanation, CO₂ methanation, and WGS/RWGS. The next step is to implement the smallest kinetic network capable of reproducing the experimentally observed products, namely CO methanation plus reversible WGS. CO₂ methanation can then be added so that formation and subsequent consumption of CO₂ are both represented.

After establishing the reaction network, the three-reaction LHHW structure reported by Celoria et al. provides the most suitable mechanistic starting point among the reviewed studies because it explicitly accounts for competition between CO and CO₂ on a shared Ni surface [7]. The species balances should then be coupled to an energy balance, followed by checks for pressure drop and transport limitations. Predicted CO conversion and CH₄/CO₂ selectivity should be compared with the Experiment-1 GC data using the same wet or dry basis and consistent performance definitions. Carbon balance closure is also important because missing carbon may indicate solid carbon or unmeasured hydrocarbons [6,7].

Once the model reproduces the experimental reactor behavior with acceptable accuracy, it can be used to generate axial profiles of CO, H₂, CH₄, H₂O, CO₂, and temperature. Sensitivity studies can then examine inlet temperature, pressure, H₂/CO ratio, flow rate or GHSV, catalyst mass, heat-transfer coefficient, kinetic parameters, and catalyst activity. Optimization should seek improved CO conversion and CH₄ selectivity while limiting CO₂ formation, excessive temperature rise, pressure drop, and operating conditions that favor catalyst deactivation.

### Research Gap and Overall Literature Synthesis

The literature provides extensive knowledge on Ni/Al₂O₃ catalyst structure, CO and CO₂ methanation, COₓ reaction mechanisms, adsorption-based kinetics, deactivation, and reactor heat management. However, these elements have largely been studied under different catalyst formulations and operating conditions. The reviewed catalysts vary in Ni loading, precursor, support composition, preparation technique, calcination and reduction history, dispersion, crystallite size, and metal-support interaction. Therefore, no single published set of kinetic parameters can be assumed to reproduce the project reactor quantitatively [3-9].

A further limitation is that many catalyst-performance studies report integral conversions at moderate or high conversion. Such results combine intrinsic reaction kinetics with residence time, equilibrium approach, and possible heat- and mass-transfer effects, and therefore cannot be used directly as intrinsic rate data. Among the reviewed works, the mixed-feed kinetic study of Celoria et al. provides the strongest basis for the mathematical form of the project kinetics because it combines transport checks, parameter regression, and a common adsorption framework for CO methanation, CO₂ methanation, and RWGS [7]. Even so, its numerical parameters require project-specific validation because the experimental catalyst and reactor conditions differ.

The central contribution of the present project is therefore not to propose an entirely new fundamental reaction mechanism, but to integrate the most defensible elements of the existing literature into a reactor model tailored to the laboratory system. The model must explain the experimentally observed CO₂ formation, account for the strong thermal coupling of methanation, and distinguish intrinsic literature kinetics from any fitted catalyst-activity correction. A validated non-isothermal fixed-bed model with reversible reactions, pressure-drop checks, and an optional activity term provides the appropriate framework for simulation, sensitivity analysis, and optimization of the Ni/Al₂O₃ CO-methanation reactor.

---

## References

1. Deiana, P., Colelli, L., Bassano, C., De Pra, Y., Testa, G., Verdone, N., & Vilardi, G. (2025). Power to Gas Pilot Plant for CO₂ Methanation with a Ni-Based Catalyst. *Industrial & Engineering Chemistry Research*, 64, 3886–3901. https://doi.org/10.1021/acs.iecr.4c03289.
2. Cue Gonzalez, A., Weiss-Hortala, E., Pham, Q. N., & Pham Minh, D. (2025). Catalytic Methanation over Natural Clay-Supported Nickel Catalysts. *Molecules*, 30, 2110. https://doi.org/10.3390/molecules30102110.
3. Usman, M., Podila, S., Al-Zahrani, A. A., & Alamoudi, M. A. (2025). CO₂ methanation over Ni/SiO₂-Al₂O₃ catalysts: effect of Ba, La, and Ce addition. *RSC Advances*, 15, 10958–10969. https://doi.org/10.1039/D4RA08895F.
4. Chang, Z., Yu, F., Yao, Y., Li, J., Zeng, J., Chen, Q., Li, J., Dai, B., & Zhang, J. (2021). Enhanced low-temperature CO/CO₂ methanation performance of Ni/Al₂O₃ microspheres prepared by the spray drying method combined with high shear mixer-assisted coprecipitation. *Fuel*, 291, 120127. https://doi.org/10.1016/j.fuel.2021.120127.
5. Yu, J., Feng, B., Liu, S., Mu, X., Lester, E., & Wu, T. (2022). Highly active Ni/Al₂O₃ catalyst for CO₂ methanation by the decomposition of Ni-MOF@Al₂O₃ precursor via cold plasma. *Applied Energy*, 315, 119036. https://doi.org/10.1016/j.apenergy.2022.119036.
6. Mo, W., Wang, X., Zou, M., Huang, X., Ma, F., Zhao, J., & Zhao, T. (2021). Influence of Ni Precursors on the Structure, Performance, and Carbon Deposition of Ni-Al₂O₃ Catalysts for CO Methanation. *ACS Omega*, 6, 16373–16380. https://doi.org/10.1021/acsomega.1c00914.
7. Celoria, F., Salomone, F., Tauro, A., Gandiglio, M., Ferrero, D., Champon, I., Geffraye, G., Pirone, R., & Bensaid, S. (2025). Kinetic study and deactivation phenomena for the methanation of CO₂ and CO mixed syngas on a Ni/Al₂O₃ catalyst. *Chemical Engineering Journal*, 512, 162113. https://doi.org/10.1016/j.cej.2025.162113.
8. Zhang, H., Dong, Y., Fang, W., & Lian, Y. (2013). Effects of composite oxide supports on catalytic performance of Ni-based catalysts for CO methanation. *Chinese Journal of Catalysis*, 34, 330–335. https://doi.org/10.1016/S1872-2067(11)60485-3.
9. Wang, H., Wu, J., Bao, Y., Feng, H., Liu, J., & Wang, H. (2023). CO₂ methanation over Ni/Al₂O₃-ZrO₂ catalysts: Optimizing metal-oxide interfaces by calcinating-induced phase transformation of support. *Journal of Environmental Chemical Engineering*, 11, 109538. https://doi.org/10.1016/j.jece.2023.109538.
10. Xu, J., & Froment, G. F. (1989). Methane steam reforming, methanation and water-gas shift: I. Intrinsic kinetics. *AIChE Journal*, 35, 88–96. https://doi.org/10.1002/aic.690350109.
11. Quindimil, A., Onrubia-Calvo, J. A., Davó-Quiñonero, A., Bermejo-López, A., Bailón-García, E., Pereda-Ayo, B., Lozano-Castelló, D., González-Marcos, J. A., Bueno-López, A., & González-Velasco, J. R. (2022). Intrinsic kinetics of CO₂ methanation on low-loaded Ni/Al₂O₃ catalyst: Mechanism, model discrimination and parameter estimation. *Journal of CO₂ Utilization*, 57, 101888. https://doi.org/10.1016/j.jcou.2022.101888.
12. Langer, M., & Freund, H. (2024). Reaction Kinetic Modeling of the COx Methanation over a Broad Range of Operation Conditions on an Impregnated Ni/Al₂O₃ Catalyst. *Industrial & Engineering Chemistry Research*, 63, 10981–10996. https://doi.org/10.1021/acs.iecr.4c00819.
13. Tommasi, M., Degerli, S. N., Ramis, G., & Rossetti, I. (2024). Advancements in CO₂ methanation: A comprehensive review of catalysis, reactor design and process optimization. *Chemical Engineering Research and Design*, 201, 457–482. https://doi.org/10.1016/j.cherd.2023.11.060.
