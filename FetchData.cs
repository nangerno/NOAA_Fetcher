using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class APIClient : MonoBehaviour
{
    private string baseUrl = "http://127.0.0.1:8000/";

    void Start()
    {
        // Call the endpoints
        StartCoroutine(GetCharts());
        StartCoroutine(GetChartById("US1AK90M_point"));
        StartCoroutine(PostChartsByLocation("latitude=65&longitude=-178"));
    }

    // Fetch all charts
    IEnumerator GetCharts()
    {
        string url = baseUrl + "charts";
        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError || 
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error fetching charts: " + webRequest.error);
            }
            else
            {
                Debug.Log("Charts: " + webRequest.downloadHandler.text);
                // Process the data if necessary
            }
        }
    }

    // Fetch a chart by ID
    IEnumerator GetChartById(string id)
    {
        string url = baseUrl + "charts/" + id + "/file";
        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError || 
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error fetching chart by ID: " + webRequest.error);
            }
            else
            {
                Debug.Log($"Chart {id}: " + webRequest.downloadHandler.text);
                // Process the data if necessary
            }
        }
    }

    // Fetch charts by location
    IEnumerator PostChartsByLocation(string location)
    {
        // Construct the URL with the query parameters
        string url = baseUrl + "charts/by-location?" + location;

        using (UnityWebRequest webRequest = UnityWebRequest.Post(url, new WWWForm()))
        {
            // Send the request
            yield return webRequest.SendWebRequest();

            // Check if there were any errors during the request
            if (webRequest.result == UnityWebRequest.Result.ConnectionError || 
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error fetching charts by location: " + webRequest.error);
            }
            else if (webRequest.responseCode == 422)
            {
                Debug.LogError("Error 422: Check if the request payload matches server requirements.");
                Debug.LogError("Server Response: " + webRequest.downloadHandler.text);  // Log server response for more details
            }
            else
            {
                // Log the successful response
                Debug.Log($"Charts for location: {webRequest.downloadHandler.text}");
            }
        }
    }


}