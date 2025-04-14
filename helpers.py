def get_aqi_class(aqi):
    """Return the CSS class for an AQI value"""
    try:
        aqi = int(aqi)
        if aqi <= 50:
            return 'good'
        elif aqi <= 100:
            return 'moderate'
        elif aqi <= 150:
            return 'unhealthy-sensitive'
        elif aqi <= 200:
            return 'unhealthy'
        elif aqi <= 300:
            return 'very-unhealthy'
        else:
            return 'hazardous'
    except (ValueError, TypeError):
        return ''

def get_aqi_description(aqi):
    """Return the description for an AQI value"""
    try:
        aqi = int(aqi)
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Moderate'
        elif aqi <= 150:
            return 'Unhealthy for Sensitive Groups'
        elif aqi <= 200:
            return 'Unhealthy'
        elif aqi <= 300:
            return 'Very Unhealthy'
        else:
            return 'Hazardous'
    except (ValueError, TypeError):
        return 'Unknown'

def get_health_implications(aqi):
    """Return health implications for an AQI value"""
    try:
        aqi = int(aqi)
        if aqi <= 50:
            return """
                <p>Air quality is considered satisfactory, and air pollution poses little or no risk.</p>
                <p>Enjoy outdoor activities.</p>
            """
        elif aqi <= 100:
            return """
                <p>Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.</p>
                <p>Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.</p>
            """
        elif aqi <= 150:
            return """
                <p>Members of sensitive groups may experience health effects. The general public is not likely to be affected.</p>
                <p>Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion.</p>
            """
        elif aqi <= 200:
            return """
                <p>Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.</p>
                <p>Active children and adults, and people with respiratory disease, such as asthma, should avoid prolonged outdoor exertion; everyone else, especially children, should limit prolonged outdoor exertion.</p>
            """
        elif aqi <= 300:
            return """
                <p>Health warnings of emergency conditions. The entire population is more likely to be affected.</p>
                <p>Active children and adults, and people with respiratory disease, such as asthma, should avoid all outdoor exertion; everyone else, especially children, should limit outdoor exertion.</p>
            """
        else:
            return """
                <p>Health alert: everyone may experience more serious health effects.</p>
                <p>Everyone should avoid all outdoor exertion.</p>
            """
    except (ValueError, TypeError):
        return "<p>No health information available.</p>"

