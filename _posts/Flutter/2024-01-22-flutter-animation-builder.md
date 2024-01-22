---

layout: post

title: "Simple custom animation in Flutter from scratch using `AnimatedBuilder`"

author: sal

date: 2024-01-11-03:25:54

categories: [ Flutter, Oneview ]

image: assets/images/flutter/flutter-animatedbuilder.gif

---


We'll create a `RotationAnimation` widget that makes its child widget rotate over a duration of 5 seconds.
Here's the step-by-step guide:
- First, you need to import the flutter/material.dart package in your Dart file:

```import 'package:flutter/material.dart';```

- Next, define the RotationAnimation widget. This widget takes a child and creates a rotation animation:

```
class RotationAnimation extends StatefulWidget {
  final Widget child;

  RotationAnimation({required this.child});

  @override
  _RotationAnimationState createState() => _RotationAnimationState();
}
```

- Now, define the state for the RotationAnimation widget. The state includes an AnimationController that controls the animation:

```
class _RotationAnimationState extends State<RotationAnimation> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 5),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      child: widget.child,
      builder: (BuildContext context, Widget? child) {
        return Transform.rotate(
          angle: _controller.value * 2.0 * 3.1416,
          child: child,
        );
      },
    );
  }
}
```

- Finally, you can use the RotationAnimation widget in your app. For example, you can make a text widget rotate:

```
void main() {
  runApp(
    MaterialApp(
      home: Scaffold(
        body: Center(
          child: RotationAnimation(
            child: Text('Hello, Flutter!'),
          ),
        ),
      ),
    ),
  );
}
```

This is a simple example of a custom animation in Flutter using `AnimatedBuilder`. You can create more complex animations by using different animation widgets and combining multiple animations.
Remember, before you start, make sure you have Flutter installed on your system. It's also useful to have a basic understanding of the framework's fundamental concepts, such as widgets, state management, and gesture handling.
I hope this helps! Let me know if you have any other questions. Happy coding! 🚀
