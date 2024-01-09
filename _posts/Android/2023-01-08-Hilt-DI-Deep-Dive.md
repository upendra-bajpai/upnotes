---

layout: post

title: "Hilt DI Deep Dive"

author: sal

date: 2020-07-24-02:25:54

categories: [ Android ]

image: assets/images/4.jpg

tags: [featured]

---
# Quick start

All apps that use Hilt must contain an Application class that is annotated with  `@HiltAndroidApp`  since it triggers Hilt’s code generation at compile time. And for Hilt to be able to inject dependencies into an activity, the activity needs to be annotated with  `@AndroidEntryPoint`.

    @HiltAndroidApp
	class MusicApp : Application()

	@AndroidEntryPoint
	class PlayActivity : AppCompatActivity() { /* ... */ }

  
## In Activity
To inject a dependency, annotate the variables that you want Hilt to inject with  ```@Inject```. All Hilt-injected variables will be available when ```super.onCreate``` is called.


```
**@AndroidEntryPoint**  
class MainActivity : AppCompatActivity() { **@Inject** lateinit var analytics: AnalyticsAdapter override fun onCreate(savedInstanceState: Bundle?) {  
    super.onCreate(savedInstanceState) // analytics instance has been populated by Hilt  
    // and it's ready to be used  
  }  
}
```

## ViewModel
```
interface Milk { ... }

interface Coffee { ... }

class LatteViewModel @ViewModelInject constructor(

private val milk: Milk,

private val coffee: Coffee

) : ViewModel() {

...

}

@AndroidEntryPoint

class LatteActivity : AppCompatActivity() {

private val viewModel: LatteViewModel by viewModels()

...

}
```

If you need access to saved state in your ViewModel, inject a SavedStateHandle as a constructor parameter by adding the @Assisted annotation.

```
class LatteViewModel @ViewModelInject constructor(

@Assisted private val savedState: SavedStateHandle,

private val milk: Milk,

private val coffee: Coffee

) : ViewModel() {

...

}
```
Components
Each module is installed inside a Hilt component, specified by using 
**@InstallIn(<component>)**. The module’s component is primarily used to prevent accidentally injecting a dependency in the wrong place. For example, *@InstallIn(ServiceComponent.class)* would prevent bindings and providers in the annotated module from being used in an activity.

In addition, a binding can be scoped to the component the module is in. Which brings me to…

Scopes
By default, bindings are unscoped. In the example above, this means every time you inject Milk, you get a new instance of OatMilk. If you add the **@ActivityScoped** annotation, you’ll scope the binding to *ActivityComponent*.

```@Module

@InstallIn(ActivityComponent::class)

abstract class MilkModule {

@ActivityScoped

@Binds

abstract fun bindMilk(oatMilk: OatMilk): Milk

}
```
Now that your module is scoped, Hilt will only create one `OatMilk` per activity instance. In addition, that `OatMilk` instance will be tied to that activity’s lifecycle — it will be created when the activity’s `onCreate()` is called and destroyed when the activity’s `onDestroy()` is called.

In this case, both  `milk`  and  `moreMilk`  will point to the same  `OatMilk`  instance. However, if you have multiple instances of  `LatteActivity`, they will each have their own instance of  `OatMilk`.

Correspondingly, other dependencies injected into this activity have the same scope, and thus they too will use the same instance of  `OatMilk`:

```
// the Milk instance will be created before a Fridge exists, as it's tied to an activity's lifecycle

class Fridge @Inject constructor(private val Milk milk) { ... }

@AndroidEntryPoint

class LatteActivity : AppCompatActivity() {

// only one instance of Milk is shared among all 4 of these:

@Inject lateinit var milk: Milk

@Inject lateinit var moreMilk: Milk

@Inject lateinit var fridge: Fridge

@Inject lateinit var backupFridge: Fridge

...

}
```
The scope also determines the lifecycle of injected instances: in this case, the single instance of `Milk` used by `Fridge` and `LatteActivity` is created when `onCreate()` is called for `LatteActivity` — and destroyed in its `onDestroy()`. This also means our `Milk` wouldn’t “survive” a configuration change, as that would involve a call to `onDestroy()` on the activity. You can overcome this by using a scope with a longer lifecycle, such as `@ActivityRetainedScope`.

Other components are [here](https://dagger.dev/hilt/components.html) 
## Make a dependency injectable Cheat Sheet

To make something injectable in Hilt, you must tell Hilt how to create an instance of that thing. These instructions are called  _bindings_.

There are three ways to define a binding in Hilt.

1.  Annotate the constructor with  `@Inject`
2.  Use  `@Binds`  in a module
3.  Use  `@Provides`  in a module

⮕  **Annotate the constructor with** `**@Inject**`

referance post [medium post](https://medium.com/androiddevelopers/a-pragmatic-guide-to-hilt-with-kotlin-a76859c324a1)

![Cheat Sheet](I/upnotes/assets/images/hiltflow.webp "Title")
<p><iframe  style="width:100%;"  height="315"  src="https://www.youtube.com/embed/Cniqsc9QfDo?rel=0&amp;showinfo=0"  frameborder="0"  allowfullscreen></iframe></p>
