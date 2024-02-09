---
layout: post
title:  "Android jetpack compose intro"
author: sal
date: 2020-07-24-02:25:54
categories: [ Jekyll, tutorial ]
image: assets/images/android/composecheat.png
---
#### Jetpack Compose
Composable Functions In Jetpack Compose, UI is defined by functions annotated with @Composable. These functions describe what the UI looks like and its behavior. Here's a simple example of a composable function:

```
@Composable
fun Greeting(name: String) {
    Text(text = "Hello $name!")
}
```

This function creates a text view that displays a greeting message. You can call this function in another composable function to include the greeting in the UI.
Next, let's move on to Layouts.
LayoutsIn Jetpack Compose, you use layout composable functions to position and align other composables. The most basic layout composable functions are Column and Row, which arrange their children vertically and horizontally respectively.
Here's an example of using Column:

```
@Composable
fun SimpleColumn() {
    Column {
        Text("Hello")
        Text("World")
    }
}
```

In this example, "Hello" and "World" will be displayed vertically in a column.
Now, let's discuss Material Design.
Material DesignJetpack Compose provides a set of Material Design components out of the box. These components follow the Material Design guidelines and include options for customization.
For example, to create a Material Design button, you can use the Button composable function:

```
@Composable
fun SimpleButton(onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text("Click me")
    }
}
```

In this example, a  #### Material Design button with the text "Click me" is created.
Next, let's talk about Lists and animations.
Lists and AnimationsJetpack Compose provides the LazyColumn and LazyRow composables for creating lists. These composables only compose and layout items that are visible, making them efficient for large lists.
Here's an example of a simple list using LazyColumn:

```
@Composable
fun SimpleList() {
    val items = listOf("Apple", "Banana", "Cherry")
    LazyColumn {
        items(items) { item ->
            Text(item)
        }
    }
}
```

In this example, a  #### vertical list of fruits is created.
For animations, Jetpack Compose provides a powerful and flexible animation API. You can animate almost any property of a composable.
Finally, let's discuss the Anatomy of a theme.
Anatomy of a ThemeIn Jetpack Compose, a theme is typically made up of a number of systems that group common visual and behavioral concepts. These systems can be modeled with classes which have theming values. For example, MaterialTheme includes Colors (color system), Typography (typography system), and Shapes (shape system).
Here's an example of defining a custom theme:

```
@Composable
fun MyTheme(content: @Composable () -> Unit) {
    val colors = lightColors(primary = Purple200)
    MaterialTheme(colors = colors, content = content)
}
```

In this example, a  #### custom theme with a primary color of Purple200 is created.

#### let's dive into advanced state and side effects in Jetpack Compose.

Advanced StateIn Jetpack Compose, state is a first-class citizen. You can create a state using the mutableStateOf function and observe it in your composable functions. When the state changes, the composable functions that observe it will automatically recompose.
```
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("Count: $count")
    }
}
```

In this example, the Counter composable has a state count. When the button is clicked, count is incremented and the Button composable is recomposed with the new count.

*Side EffectsSide* effects are changes to the state of the app that happen outside the scope of a composable function. Due to composables' lifecycle and properties such as unpredictable recompositions, executing recompositions of composables in different orders, or recompositions that can be discarded, composables should ideally be side-effect free.

However, sometimes side effects are necessary, for example, to trigger a one-off event such as showing a snackbar or navigate to another screen given a certain state condition. These actions should be called from a controlled environment that is aware of the lifecycle of the composable.

#### Here are some side effect APIs Jetpack Compose offers
LaunchedEffectTo call suspend functions safely from inside a composable, use the LaunchedEffect composable. When LaunchedEffect enters the Composition, it launches a coroutine with the block of code passed as a parameter. The coroutine will be cancelled if LaunchedEffect leaves the composition.

```
@Composable
fun MyComposable() {
    val coroutineScope = rememberCoroutineScope()
    LaunchedEffect(Unit) {
        coroutineScope.launch {
            // Your suspend function goes here
        }
    }
}
```
In this example, MyComposable launches a coroutine when it enters the composition. The coroutine is cancelled when MyComposable leaves the composition.

#### Jetpack Compose NavigationJetpack 
Compose Navigation allows you to navigate between different screens in your Compose app. Here's a basic example:
```
@Composable
fun MyApp() {
    val navController = rememberNavController()
    NavHost(navController, startDestination = "login") {
        composable("login") { LoginScreen(navController) }
        composable("dashboard") { DashboardScreen() }
    }
}
```
In this example, MyApp creates a NavController and a NavHost. The NavHost defines the navigation graph of the app. When you want to navigate to a different screen, you can call navController.navigate("route"), where "route" is the route of the destination screen.
Jetpack Compose Material DesignJetpack Compose provides a set of Material Design components out of the box. These components follow the Material Design guidelines and include options for customization.
For example, to create a Material Design button, you can use the Button composable function:

```
@Composable
fun SimpleButton(onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text("Click me")
    }
}
```
In this example, a Material Design button with the text "Click me" is created.

Jetpack Compose Performance OptimizationJetpack Compose aims to deliver great performance out of the box. However, there are several techniques you can use to optimize your Compose app.

- Build in release mode and use R8: Debug mode is useful for spotting many problems, but it imposes a significant performance cost and can make it hard to spot other code issues that might hurt performance.
- Use a baseline profile: Baseline Profiles improve code execution speed by about 30% from the first launch by avoiding interpretation and just-in-time (JIT) compilation steps for included code paths.
- Use derivedStateOf: This can reduce a lot of your recompositions. This is useful when the state changes rapidly but doesn’t affect your composable.
- Use keys in LazyLists: This is a simple small change that can increase your LazyColumn/LazyRow performance.
- Use immutable values as much as possible in Data classes: When you have var variables in Data classes then compose thinks it can change as var is mutable so during recompositions compose thinks as the value is mutable the value may have changes and on the flow, it recomposes them even though the value has not changed.

