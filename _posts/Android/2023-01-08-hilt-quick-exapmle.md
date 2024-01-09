---

layout: post

title: "Hilt DI Deep Dive"

author: jane

date: 2023-01-08-14:25:54

categories: [ Android,DI ]

image: assets/images/4.jpg

tags: [featured]

---

#Building a Weather App. 
This app will display the current weather information for a given location. Here's how you might structure it using MVVM and Hilt:
- Create Application Instance: Annotate your Application class with @HiltAndroidApp.

@HiltAndroidApp
class WeatherApplication : Application() { ... }

- Create Activity: Annotate your Activity class with @AndroidEntryPoint. This will be the main activity displaying weather information.

@AndroidEntryPoint
class MainActivity : AppCompatActivity() { ... }

- Create ViewModel: Implement the ViewModel class. This ViewModel will handle the logic for fetching the weather data and updating the UI.

class WeatherViewModel @Inject constructor(private val repository: WeatherRepository) : ViewModel() {
    // LiveData to hold the weather data
    val weatherData: LiveData<Weather> = repository.weatherData
}

- Create Offline Repository (with Room): Implement a Room Database for offline data storage. This will store the weather data locally.

@Database(entities = [Weather::class], version = 1)
abstract class WeatherDatabase : RoomDatabase() {
    abstract fun weatherDao(): WeatherDao
}

- Create Online Repository (with Retrofit): Implement a Retrofit interface for online data fetching. This will fetch the weather data from a weather API.

interface WeatherService {
    @GET("weather")
    suspend fun getWeather(@Query("q") location: String): Response<Weather>
}

- Inject Dependencies with Hilt: Use Hilt for dependency injection. This will provide the necessary dependencies to your classes.

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    fun provideWeatherService(): WeatherService = Retrofit.Builder()
        .baseUrl("https://api.openweathermap.org/data/2.5/")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(WeatherService::class.java)

    @Provides
    fun provideDatabase(@ApplicationContext appContext: Context): WeatherDatabase = Room.databaseBuilder(
        appContext,
        WeatherDatabase::class.java,
        "weather_database"
    ).build()

    @Provides
    fun provideWeatherDao(db: WeatherDatabase): WeatherDao = db.weatherDao()
}

This is a simplified example. For a more detailed explanation, you can refer to the articles I found. Happy coding! 🚀