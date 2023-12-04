import streamlit as st
import requests
import datetime


# Funktion för att hämta kanaler med ljudströmmar från SR API
@st.cache_data  # Är streamlit cache funktion för att spara data i minnet
def fetch_all_channels():
    response = requests.get("https://api.sr.se/api/v2/channels?format=json&pagination=false")
    data = response.json()
    channels = []
    if "channels" in data:
        for channel in data["channels"]:
            channel_info = {
                "name": channel["name"],
                "id": channel["id"],
                "audio_url": channel.get("liveaudio", {}).get("url", "")  # Hämta ljudströmmen för kanalen
            }
            channels.append(channel_info)
    return channels


#  Här hämtar vi information om programen + för en specifik kanal och datum
@st.cache_data
def fetch_schedule_for_channel(channel_id, date):
    date_str = date.strftime("%Y-%m-%d")
    size = 100
    page = 1
    all_schedule = []
    while True:
        api_url = (f"https://api.sr.se/api/v2/scheduledepisodes?channelid="
                   f"{channel_id}&date={date_str}&format=json&size={size}&page={page}")
        response = requests.get(api_url)
        data = response.json()
        schedule = data.get("schedule", [])
        all_schedule.extend(schedule)
        if "pagination" not in data or not data["pagination"].get("nextpage"):
            break
        page += 1
    return all_schedule


# Hjälpfunktioner
def convert_to_readable_time(unix_time_string):
    try:
        timestamp = int(unix_time_string.replace("/Date(", "").replace(")/", "")) // 1000
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OverflowError):
        return "Ogiltig starttid"


# Streamlit app layout
def main():
    st.title("Sveriges Radio Program Info")

    # Välj en kanal för att lyssna på ljudströmmen
    channels = fetch_all_channels()
    channel_options = [channel["name"] for channel in channels]
    selected_channel_name = st.selectbox("Lyssna på en kanal:", channel_options)

    if selected_channel_name:
        selected_channel = next((channel for channel in channels if channel["name"] == selected_channel_name), None)
        if selected_channel and "audio_url" in selected_channel:
            st.audio(selected_channel["audio_url"])

    # Välj en kanal för att se schemat
    channel_name = st.selectbox("Se schemat för en kanal:", channel_options)
    start_date = st.date_input("Välj startdatum", datetime.date.today())

    if st.button("Visa program"):
        if channel_name:
            with st.spinner("Hämtar program..."):
                channel_id = next((channel["id"] for channel in channels if channel["name"] == channel_name), None)
                schedule = fetch_schedule_for_channel(channel_id, start_date)
                if schedule:
                    for program in schedule:
                        st.subheader(program["title"])
                        st.write("Starttid:", convert_to_readable_time(program["starttimeutc"]))
                        st.write("Beskrivning:", program.get("description", "Ingen beskrivning tillgänglig,"
                                                                            " sorry gullegrisen<3"))
                        st.write("----")
                else:
                    st.write("Inga program hittades för valt datum och kanal, från SR. sorry gullet <3.")


if __name__ == "__main__":
    main()
