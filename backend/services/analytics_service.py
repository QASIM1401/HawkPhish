"""HawkPhish - Analytics & Heatmap Service"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models import EmailLog, Campaign, Recipient, RecipientSession

# Country coordinates for heatmap
COUNTRY_COORDS = {
    "US": {"lat": 37.0902, "lon": -95.7129, "name": "United States"},
    "CA": {"lat": 56.1304, "lon": -106.3468, "name": "Canada"},
    "GB": {"lat": 55.3781, "lon": -3.4360, "name": "United Kingdom"},
    "DE": {"lat": 51.1657, "lon": 10.4515, "name": "Germany"},
    "FR": {"lat": 46.2276, "lon": 2.2137, "name": "France"},
    "AU": {"lat": -25.2744, "lon": 133.7751, "name": "Australia"},
    "JP": {"lat": 36.2048, "lon": 138.2529, "name": "Japan"},
    "IN": {"lat": 20.5937, "lon": 78.9629, "name": "India"},
    "BR": {"lat": -14.2350, "lon": -51.9253, "name": "Brazil"},
    "RU": {"lat": 61.5240, "lon": 105.3188, "name": "Russia"},
    "CN": {"lat": 35.8617, "lon": 104.1954, "name": "China"},
    "NL": {"lat": 52.1326, "lon": 5.2913, "name": "Netherlands"},
    "SG": {"lat": 1.3521, "lon": 103.8198, "name": "Singapore"},
    "AE": {"lat": 23.4241, "lon": 53.8478, "name": "UAE"},
    "KR": {"lat": 35.9078, "lon": 127.7669, "name": "South Korea"},
    "IT": {"lat": 41.8719, "lon": 12.5674, "name": "Italy"},
    "ES": {"lat": 40.4637, "lon": -3.7492, "name": "Spain"},
    "SE": {"lat": 60.1282, "lon": 18.6435, "name": "Sweden"},
    "CH": {"lat": 46.8182, "lon": 8.2275, "name": "Switzerland"},
    "NO": {"lat": 60.4720, "lon": 8.4689, "name": "Norway"},
    "ZA": {"lat": -30.5595, "lon": 22.9375, "name": "South Africa"},
    "MX": {"lat": 23.6345, "lon": -102.5528, "name": "Mexico"},
    "TR": {"lat": 38.9637, "lon": 35.2433, "name": "Turkey"},
    "PL": {"lat": 51.9194, "lon": 19.1451, "name": "Poland"},
    "ID": {"lat": -0.7893, "lon": 113.9213, "name": "Indonesia"},
    "PK": {"lat": 30.3753, "lon": 69.3451, "name": "Pakistan"},
    "NG": {"lat": 9.0820, "lon": 8.6753, "name": "Nigeria"},
    "BD": {"lat": 23.6850, "lon": 90.3563, "name": "Bangladesh"},
    "EG": {"lat": 26.8206, "lon": 30.8025, "name": "Egypt"},
    "VN": {"lat": 14.0583, "lon": 108.2772, "name": "Vietnam"},
    "PH": {"lat": 12.8797, "lon": 121.7740, "name": "Philippines"},
    "TH": {"lat": 15.8700, "lon": 100.9925, "name": "Thailand"},
    "MY": {"lat": 4.2105, "lon": 101.9758, "name": "Malaysia"},
    "SA": {"lat": 23.8859, "lon": 45.0792, "name": "Saudi Arabia"},
    "UA": {"lat": 48.3794, "lon": 31.1656, "name": "Ukraine"},
    "RO": {"lat": 45.9432, "lon": 24.9668, "name": "Romania"},
    "CZ": {"lat": 49.8175, "lon": 15.4730, "name": "Czech Republic"},
    "BE": {"lat": 50.5039, "lon": 4.4699, "name": "Belgium"},
    "AT": {"lat": 47.5162, "lon": 14.5501, "name": "Austria"},
    "PT": {"lat": 39.3999, "lon": -8.2245, "name": "Portugal"},
    "GR": {"lat": 39.0742, "lon": 21.8243, "name": "Greece"},
    "IE": {"lat": 53.1424, "lon": -7.6921, "name": "Ireland"},
    "DK": {"lat": 56.2639, "lon": 9.5018, "name": "Denmark"},
    "FI": {"lat": 61.9241, "lon": 25.7482, "name": "Finland"},
    "NZ": {"lat": -40.9006, "lon": 174.8869, "name": "New Zealand"},
    "IL": {"lat": 31.0461, "lon": 34.8516, "name": "Israel"},
    "HK": {"lat": 22.3193, "lon": 114.1694, "name": "Hong Kong"},
    "TW": {"lat": 23.6978, "lon": 120.9605, "name": "Taiwan"},
    "AR": {"lat": -38.4161, "lon": -63.6167, "name": "Argentina"},
    "CL": {"lat": -35.6751, "lon": -71.5430, "name": "Chile"},
    "CO": {"lat": 4.5709, "lon": -74.2973, "name": "Colombia"},
    "PE": {"lat": -9.1900, "lon": -75.0152, "name": "Peru"},
    "KE": {"lat": -0.0236, "lon": 37.9062, "name": "Kenya"},
    "GH": {"lat": 7.9465, "lon": -1.0232, "name": "Ghana"},
    "TZ": {"lat": -6.3690, "lon": 34.8888, "name": "Tanzania"},
    "UG": {"lat": 1.3733, "lon": 32.2903, "name": "Uganda"},
    "MA": {"lat": 31.7917, "lon": -7.0926, "name": "Morocco"},
    "DZ": {"lat": 28.0339, "lon": 1.6596, "name": "Algeria"},
    "TN": {"lat": 33.8869, "lon": 9.5375, "name": "Tunisia"},
    "LK": {"lat": 7.8731, "lon": 80.7718, "name": "Sri Lanka"},
    "NP": {"lat": 28.3949, "lon": 84.1240, "name": "Nepal"},
    "MM": {"lat": 21.9130, "lon": 95.9560, "name": "Myanmar"},
    "KH": {"lat": 12.5657, "lon": 104.9910, "name": "Cambodia"},
    "LA": {"lat": 19.8563, "lon": 102.4955, "name": "Laos"},
    "MN": {"lat": 46.8625, "lon": 103.8467, "name": "Mongolia"},
    "KZ": {"lat": 48.0196, "lon": 66.9237, "name": "Kazakhstan"},
    "UZ": {"lat": 41.3775, "lon": 64.5853, "name": "Uzbekistan"},
    "AZ": {"lat": 40.1431, "lon": 47.5769, "name": "Azerbaijan"},
    "GE": {"lat": 42.3154, "lon": 43.3569, "name": "Georgia"},
    "AM": {"lat": 40.0691, "lon": 45.0382, "name": "Armenia"},
    "BY": {"lat": 53.7098, "lon": 27.9534, "name": "Belarus"},
    "LT": {"lat": 55.1694, "lon": 23.8813, "name": "Lithuania"},
    "LV": {"lat": 56.8796, "lon": 24.6032, "name": "Latvia"},
    "EE": {"lat": 58.5953, "lon": 25.0136, "name": "Estonia"},
    "SK": {"lat": 48.6690, "lon": 19.6990, "name": "Slovakia"},
    "SI": {"lat": 46.1512, "lon": 14.9955, "name": "Slovenia"},
    "HR": {"lat": 45.1000, "lon": 15.2000, "name": "Croatia"},
    "BA": {"lat": 43.9159, "lon": 17.6791, "name": "Bosnia"},
    "RS": {"lat": 44.0165, "lon": 21.0059, "name": "Serbia"},
    "ME": {"lat": 42.7087, "lon": 19.3744, "name": "Montenegro"},
    "MK": {"lat": 41.6086, "lon": 21.7453, "name": "North Macedonia"},
    "AL": {"lat": 41.1533, "lon": 20.1683, "name": "Albania"},
    "BG": {"lat": 42.7339, "lon": 25.4858, "name": "Bulgaria"},
    "MD": {"lat": 47.4116, "lon": 28.3699, "name": "Moldova"},
    "IS": {"lat": 64.9631, "lon": -19.0208, "name": "Iceland"},
    "LU": {"lat": 49.8153, "lon": 6.1296, "name": "Luxembourg"},
    "MT": {"lat": 35.9375, "lon": 14.3754, "name": "Malta"},
    "CY": {"lat": 35.1264, "lon": 33.4299, "name": "Cyprus"},
    "KW": {"lat": 29.3117, "lon": 47.4818, "name": "Kuwait"},
    "QA": {"lat": 25.3548, "lon": 51.1839, "name": "Qatar"},
    "BH": {"lat": 25.9304, "lon": 50.6378, "name": "Bahrain"},
    "OM": {"lat": 21.4735, "lon": 55.9754, "name": "Oman"},
    "JO": {"lat": 30.5852, "lon": 36.2384, "name": "Jordan"},
    "LB": {"lat": 33.8547, "lon": 35.8623, "name": "Lebanon"},
    "IQ": {"lat": 33.2232, "lon": 43.6793, "name": "Iraq"},
    "IR": {"lat": 32.4279, "lon": 53.6880, "name": "Iran"},
    "AF": {"lat": 33.9391, "lon": 67.7100, "name": "Afghanistan"},
    "PK": {"lat": 30.3753, "lon": 69.3451, "name": "Pakistan"},
    "BT": {"lat": 27.5142, "lon": 90.4336, "name": "Bhutan"},
    "MV": {"lat": 3.2028, "lon": 73.2207, "name": "Maldives"},
    "FJ": {"lat": -17.7134, "lon": 178.0650, "name": "Fiji"},
    "PG": {"lat": -6.3140, "lon": 143.9555, "name": "Papua New Guinea"},
    "SB": {"lat": -9.6457, "lon": 160.1562, "name": "Solomon Islands"},
    "VU": {"lat": -15.3767, "lon": 166.9592, "name": "Vanuatu"},
    "NC": {"lat": -20.9043, "lon": 165.6180, "name": "New Caledonia"},
    "PF": {"lat": -17.6797, "lon": -149.4068, "name": "French Polynesia"},
    "WS": {"lat": -13.7590, "lon": -172.1046, "name": "Samoa"},
    "TO": {"lat": -21.1790, "lon": -175.1982, "name": "Tonga"},
    "KI": {"lat": -3.3704, "lon": -168.7340, "name": "Kiribati"},
    "TV": {"lat": -7.1095, "lon": 177.6493, "name": "Tuvalu"},
    "NR": {"lat": -0.5228, "lon": 166.9315, "name": "Nauru"},
    "PW": {"lat": 7.5150, "lon": 134.5825, "name": "Palau"},
    "FM": {"lat": 7.4256, "lon": 150.5508, "name": "Micronesia"},
    "MH": {"lat": 7.1315, "lon": 171.1845, "name": "Marshall Islands"},
    "CK": {"lat": -21.2367, "lon": -159.7777, "name": "Cook Islands"},
    "NU": {"lat": -19.0544, "lon": -169.8672, "name": "Niue"},
    "TK": {"lat": -9.2002, "lon": -171.8484, "name": "Tokelau"},
    "WF": {"lat": -13.7688, "lon": -177.1561, "name": "Wallis and Futuna"},
    "AS": {"lat": -14.2710, "lon": -170.1322, "name": "American Samoa"},
    "GU": {"lat": 13.4443, "lon": 144.7937, "name": "Guam"},
    "MP": {"lat": 15.0979, "lon": 145.6739, "name": "Northern Mariana Islands"},
    "PR": {"lat": 18.2208, "lon": -66.5901, "name": "Puerto Rico"},
    "VI": {"lat": 18.3358, "lon": -64.8963, "name": "US Virgin Islands"},
    "KY": {"lat": 19.5139, "lon": -80.5669, "name": "Cayman Islands"},
    "BM": {"lat": 32.3078, "lon": -64.7505, "name": "Bermuda"},
    "GL": {"lat": 71.7069, "lon": -42.6043, "name": "Greenland"},
    "FO": {"lat": 61.8926, "lon": -6.9118, "name": "Faroe Islands"},
    "GI": {"lat": 36.1377, "lon": -5.3456, "name": "Gibraltar"},
    "JE": {"lat": 49.2144, "lon": -2.1312, "name": "Jersey"},
    "GG": {"lat": 49.4657, "lon": -2.5853, "name": "Guernsey"},
    "IM": {"lat": 54.2361, "lon": -4.5481, "name": "Isle of Man"},
    "AX": {"lat": 60.1785, "lon": 19.9156, "name": "Aland Islands"},
    "SJ": {"lat": 77.8757, "lon": 20.9752, "name": "Svalbard"},
    "BV": {"lat": -54.4237, "lon": 3.4132, "name": "Bouvet Island"},
    "HM": {"lat": -53.0818, "lon": 73.5042, "name": "Heard Island"},
    "IO": {"lat": -6.3432, "lon": 71.8765, "name": "British Indian Ocean Territory"},
    "TF": {"lat": -49.2804, "lon": 69.3486, "name": "French Southern Territories"},
    "AQ": {"lat": -75.2509, "lon": -0.0713, "name": "Antarctica"},
    "GS": {"lat": -54.4296, "lon": -36.5879, "name": "South Georgia"},
    "UM": {"lat": 19.2823, "lon": 166.6470, "name": "US Minor Outlying Islands"},
    "CC": {"lat": -12.1642, "lon": 96.8710, "name": "Cocos Islands"},
    "CX": {"lat": -10.4475, "lon": 105.6904, "name": "Christmas Island"},
    "NF": {"lat": -29.0408, "lon": 167.9547, "name": "Norfolk Island"},
    "PN": {"lat": -24.3768, "lon": -128.3242, "name": "Pitcairn"},
    "TC": {"lat": 21.6940, "lon": -71.7979, "name": "Turks and Caicos"},
    "VG": {"lat": 18.4207, "lon": -64.6400, "name": "British Virgin Islands"},
    "AI": {"lat": 18.2206, "lon": -63.0686, "name": "Anguilla"},
    "MS": {"lat": 16.7425, "lon": -62.1874, "name": "Montserrat"},
    "SH": {"lat": -24.1435, "lon": -10.0307, "name": "Saint Helena"},
    "FK": {"lat": -51.7963, "lon": -59.5236, "name": "Falkland Islands"},
    "EH": {"lat": 24.2155, "lon": -12.8858, "name": "Western Sahara"},
    "PS": {"lat": 31.9474, "lon": 35.2272, "name": "Palestine"},
    "TW": {"lat": 23.6978, "lon": 120.9605, "name": "Taiwan"},
    "HK": {"lat": 22.3193, "lon": 114.1694, "name": "Hong Kong"},
    "MO": {"lat": 22.1987, "lon": 113.5439, "name": "Macau"},
    "MO": {"lat": 22.1987, "lon": 113.5439, "name": "Macau"},
    "RE": {"lat": -21.1151, "lon": 55.5364, "name": "Reunion"},
    "YT": {"lat": -12.8275, "lon": 45.1662, "name": "Mayotte"},
    "GP": {"lat": 16.2650, "lon": -61.5510, "name": "Guadeloupe"},
    "MQ": {"lat": 14.6415, "lon": -61.0242, "name": "Martinique"},
    "GF": {"lat": 3.9339, "lon": -53.1258, "name": "French Guiana"},
    "PM": {"lat": 46.9419, "lon": -56.2711, "name": "Saint Pierre and Miquelon"},
    "BL": {"lat": 17.9000, "lon": -62.8333, "name": "Saint Barthelemy"},
    "MF": {"lat": 18.0708, "lon": -63.0501, "name": "Saint Martin"},
    "SX": {"lat": 18.0425, "lon": -63.0548, "name": "Sint Maarten"},
    "CW": {"lat": 12.1696, "lon": -68.9900, "name": "Curacao"},
    "BQ": {"lat": 12.1784, "lon": -68.2385, "name": "Bonaire"},
    "AW": {"lat": 12.5211, "lon": -69.9683, "name": "Aruba"},
    "CW": {"lat": 12.1696, "lon": -68.9900, "name": "Curacao"},
    "SX": {"lat": 18.0425, "lon": -63.0548, "name": "Sint Maarten"},
    "BL": {"lat": 17.9000, "lon": -62.8333, "name": "Saint Barthelemy"},
    "MF": {"lat": 18.0708, "lon": -63.0501, "name": "Saint Martin"},
    "GP": {"lat": 16.2650, "lon": -61.5510, "name": "Guadeloupe"},
    "MQ": {"lat": 14.6415, "lon": -61.0242, "name": "Martinique"},
    "GF": {"lat": 3.9339, "lon": -53.1258, "name": "French Guiana"},
    "RE": {"lat": -21.1151, "lon": 55.5364, "name": "Reunion"},
    "YT": {"lat": -12.8275, "lon": 45.1662, "name": "Mayotte"},
    "PM": {"lat": 46.9419, "lon": -56.2711, "name": "Saint Pierre and Miquelon"},
    "EH": {"lat": 24.2155, "lon": -12.8858, "name": "Western Sahara"},
    "PS": {"lat": 31.9474, "lon": 35.2272, "name": "Palestine"},
    "TW": {"lat": 23.6978, "lon": 120.9605, "name": "Taiwan"},
    "HK": {"lat": 22.3193, "lon": 114.1694, "name": "Hong Kong"},
    "MO": {"lat": 22.1987, "lon": 113.5439, "name": "Macau"},
}


class AnalyticsService:
    """Analytics and heatmap service for HawkPhish"""

    @staticmethod
    async def get_geolocation_heatmap(db: AsyncSession, campaign_id: int = None) -> Dict:
        """Get heatmap data for campaign(s)."""
        query = select(EmailLog)
        if campaign_id:
            query = query.where(EmailLog.campaign_id == campaign_id)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        country_stats = {}
        for log in logs:
            country = log.country or "Unknown"
            if country == "Unknown" or not country:
                continue
            if country not in country_stats:
                country_stats[country] = {"opens": 0, "clicks": 0, "submits": 0, "total": 0}
            
            country_stats[country]["total"] += 1
            if log.status == "opened":
                country_stats[country]["opens"] += 1
            elif log.status == "clicked":
                country_stats[country]["clicks"] += 1
            elif log.status == "submitted":
                country_stats[country]["submits"] += 1
        
        # Build heatmap points
        heatmap_points = []
        for country_code, stats in country_stats.items():
            coords = COUNTRY_COORDS.get(country_code.upper(), {"lat": 0, "lon": 0, "name": country_code})
            heatmap_points.append({
                "country": coords["name"],
                "country_code": country_code.upper(),
                "lat": coords["lat"],
                "lon": coords["lon"],
                "intensity": stats["total"],
                "opens": stats["opens"],
                "clicks": stats["clicks"],
                "submits": stats["submits"],
            })
        
        return {
            "points": heatmap_points,
            "total_countries": len(heatmap_points),
            "total_events": sum(p["intensity"] for p in heatmap_points),
        }

    @staticmethod
    async def get_time_to_click_analytics(db: AsyncSession, campaign_id: int = None) -> Dict:
        """Analyze time between sent and clicked/opened."""
        query = select(EmailLog).where(EmailLog.status.in_(["opened", "clicked", "submitted"]))
        if campaign_id:
            query = query.where(EmailLog.campaign_id == campaign_id)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        time_data = {"open_times": [], "click_times": [], "submit_times": []}
        
        for log in logs:
            if log.sent_at and log.opened_at:
                delta = (log.opened_at - log.sent_at).total_seconds()
                time_data["open_times"].append(delta)
            if log.sent_at and log.clicked_at:
                delta = (log.clicked_at - log.sent_at).total_seconds()
                time_data["click_times"].append(delta)
            if log.sent_at and log.submitted_at:
                delta = (log.submitted_at - log.sent_at).total_seconds()
                time_data["submit_times"].append(delta)
        
        def stats(arr):
            if not arr:
                return {"avg": 0, "min": 0, "max": 0, "median": 0, "count": 0}
            arr.sort()
            n = len(arr)
            return {
                "avg": round(sum(arr) / n, 1),
                "min": round(min(arr), 1),
                "max": round(max(arr), 1),
                "median": round(arr[n // 2], 1),
                "count": n,
            }
        
        return {
            "open_times": stats(time_data["open_times"]),
            "click_times": stats(time_data["click_times"]),
            "submit_times": stats(time_data["submit_times"]),
            "unit": "seconds",
        }

    @staticmethod
    async def get_repeat_victim_detection(db: AsyncSession, min_campaigns: int = 2) -> Dict:
        """Detect recipients who fell for multiple campaigns."""
        query = select(EmailLog).where(EmailLog.status.in_(["clicked", "submitted"]))
        result = await db.execute(query)
        logs = result.scalars().all()
        
        victim_map = {}
        for log in logs:
            if log.recipient_id not in victim_map:
                victim_map[log.recipient_id] = {
                    "campaigns": set(),
                    "total_clicks": 0,
                    "total_submits": 0,
                }
            victim_map[log.recipient_id]["campaigns"].add(log.campaign_id)
            if log.status == "clicked":
                victim_map[log.recipient_id]["total_clicks"] += 1
            if log.status == "submitted":
                victim_map[log.recipient_id]["total_submits"] += 1
        
        repeat_victims = []
        for recipient_id, data in victim_map.items():
            if len(data["campaigns"]) >= min_campaigns:
                recipient = await db.get(Recipient, recipient_id)
                if recipient:
                    repeat_victims.append({
                        "recipient_id": recipient_id,
                        "email": recipient.email,
                        "name": f"{recipient.first_name or ''} {recipient.last_name or ''}".strip(),
                        "campaigns_affected": len(data["campaigns"]),
                        "total_clicks": data["total_clicks"],
                        "total_submits": data["total_submits"],
                    })
        
        repeat_victims.sort(key=lambda x: x["campaigns_affected"], reverse=True)
        
        return {
            "repeat_victims": repeat_victims,
            "total_repeat_victims": len(repeat_victims),
            "min_campaigns": min_campaigns,
        }

    @staticmethod
    async def get_advanced_campaign_filters(db: AsyncSession, filters: Dict) -> List:
        """Advanced filtering for campaigns."""
        query = select(Campaign)
        
        if filters.get("status"):
            query = query.where(Campaign.status == filters["status"])
        if filters.get("date_from"):
            query = query.where(Campaign.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.where(Campaign.created_at <= filters["date_to"])
        if filters.get("template_id"):
            query = query.where(Campaign.template_id == filters["template_id"])
        if filters.get("group_id"):
            query = query.where(Campaign.group_id == filters["group_id"])
        if filters.get("smtp_id"):
            query = query.where(Campaign.smtp_id == filters["smtp_id"])
        
        query = query.order_by(Campaign.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
