import streamlit as st

st.header("Tanke")
st.write("""Ideen er å lage et python-bibliotek for grunnvarme som samler 
         alle relevante beregninger og muliggjør kombinering av disse i ulike sammensetninger.
         Dette for å være fleksibel til å løse ulike problemer i ulike oppdrag.""")

st.write(""" Denne siden viser noen av mulighetene som finnes""")

st.write(""" Anvendelser:""")
st.write(" - Bergvarmekalkulatoren 2.0")
st.write(" - Tidligfasedimensjonering")
st.write(" - Energianalysen")
st.write(" - Serviettkalkylen")
st.write(" - Modulbasert i oppdrag")

st.subheader("Roadmap")

st.checkbox("Implementere en stuktur for systemet", value = True)
st.caption("""Systemet konsenteres rundt klassen Building() som skal 
         inneholde alle relevante parametere som klassevariabler.""")
st.caption("""Videre tar alle andre klasser en instans av Building() som input. 
           Dvs. f.eks. EnergyDemand(building_instance), Geoenergy(building_instance), OperationCosts(building_instance).""")

st.checkbox("PROFet-beregning i Building()", value = True)
st.caption(""" Det er mulig å kjøre PROFet beregningen med og uten egendefinert temperatur for enkeltbygg og kombinasjonsbygg.""")

st.checkbox("Geografisk PROFet-beregning med stedegen temperatur", value = False)
st.caption(""" Planen er å bruke lat/long på Building() for å hente inn stedegen temperatur som brukes inn i PROFet-spørringen""")

st.checkbox("Egendefinert energibehov", value = True)
st.caption(""" Det er mulig å legge inn egendefinert energibehov uten å bruke PROFet""")

st.checkbox("Dekningsgrad-funksjon", value = True)
st.caption(""" Dekningsgrad-funksjon som kan beregne energidekningsgrad for en valgfri timeserie""")

st.checkbox("""Klassen GeoEnergi()""", value = True)
st.caption("""Tar inn en instans av Building() og 
            legger tilbake strøm fra varmepumpe, levert energi fra brønner, spisslast, antall brønner, varmepumpestørrelse,
            investeringskostnader borehull, investeringskostnader øvrig""")

st.checkbox(""" Legge til dimensjoneringsmulighet i GeoEnergy() med pygfunction/GHEtool""", value = False)
st.caption(""" Planen er å bruke pygfunction/GHEtool for å beregne brønnmeter i GeoEnergy()-klassen. 
           Det må også være mulighet for å bestemme egendefinert geometri, og ellers bruke de gode løsningene som finnes i pygfunction.""")

st.checkbox(""" Klassen SolarPanels()""", value = True)
st.caption(""" Tar inn Building(). Mulig å 
           sette egendefinert timeserie for produksjon av solceller""")

st.checkbox(""" Utbedre SolarPanels() til å regne solproduksjon automatisk""", value = False)
st.caption(""" Planen er å bruke det som er utviklet i Into ZERO med ulike takflater for å beregne timeserie for sol.""")

st.checkbox(""" Klassen OperationCosts()""", value = True)
st.caption(""" OperationCosts() tar inn en instans av Building(), og 
           beregner driftskostnader for strøm med spotpris og nettleie for dict_energy (som ligger på bygningsobjektet).""")

st.checkbox(""" Legge til spotpriser og nettleiemodeller fra flere områder i OperationCosts()""", value = False)
st.caption(""" Legge til spotpriser for flere land. Kunne sette sin egen nettleiemodell""")

st.checkbox(""" Klassen GreenEnergyFund()""", value = True)
st.caption(""" Klassen GreenEnergyFund() som tar inn en instans av Building(). 
           Denne skal utføre serviettkalkylen på parameterene som ligger inne på Building().""")

st.checkbox(""" Utbedre GreenEnergyFund()""", value = False)
st.caption(""" Få inn alle beregninger fra serviettkalkylen.""")

st.checkbox(""" Klassen Visualization()""", value = False)
st.caption(""" Lage en klasse som brukes for visualisering. 
           Denne skal ta inn Building()) og ha funksjoner for ulike visninger. 
           Planen er å lage et sett med standard-plot.""")

st.checkbox(""" Klassen OperationCO2()""", value = False)
st.caption(""" Få inn CO2 utslipp på strøm for ulike regioner. Denne kan kjøres på samme måte som OperationCosts""")