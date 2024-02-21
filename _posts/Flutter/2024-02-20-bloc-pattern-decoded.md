---
layout: post
title:  "Bloc_Pattern_Decoded"
author: sal
date: 2024-02-20-19:08:19
categories: [  tutorial ]
image: assets/images/flutter/bloc.jpg
---

 Let’s take a look at a simple example of how to implement the BLoC pattern in Flutter. This example will demonstrate a CounterBloc that increments a counter value.

First, we define our events. In this case, we have a single event, IncrementEvent:

```

abstract class CounterEvent {}

class IncrementEvent extends CounterEvent {}
```
Next, we define our BLoC. The BLoC takes CounterEvents as input and transforms them into a stream of integers. When an IncrementEvent is received, the BLoC increments its counter:

```

class CounterBloc {
  int _counter = 0;

  final _counterStateController = StreamController<int>();
  StreamSink<int> get _inCounter => _counterStateController.sink;
  Stream<int> get counter => _counterStateController.stream;

  final _counterEventController = StreamController<CounterEvent>();
  Sink<CounterEvent> get counterEventSink => _counterEventController.sink;

  CounterBloc() {
    _counterEventController.stream.listen(_mapEventToState);
  }

  void _mapEventToState(CounterEvent event) {
    if (event is IncrementEvent)
      _counter++;
    
    _inCounter.add(_counter);
  }

  void dispose() {
    _counterStateController.close();
    _counterEventController.close();
  }
}
```

_counterStateController is a StreamController that manages the state of the counter. The sink of a StreamController is where data is added, and the stream is where data comes out.
_counterEventController is another StreamController that manages the incoming events. Events are added to the sink, and the stream is where the Bloc listens for new events.
In the CounterBloc constructor, we start listening to the _counterEventController’s stream. Whenever a new event is added to the sink, the _mapEventToState function is called with that event.
_mapEventToState is where events are converted into state changes. If the event is an IncrementEvent, we increment the _counter and add the new value to the _counterStateController’s sink.
The dispose method is used to close the StreamControllers when they’re no longer needed, preventing memory leaks.

In your widget, you can now use this CounterBloc to respond to user interactions and update the UI:

```

class MyWidget extends StatelessWidget {
  final _bloc = CounterBloc();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        StreamBuilder<int>(
          stream: _bloc.counter,
          initialData: 0,
          builder: (BuildContext context, AsyncSnapshot<int> snapshot) {
            return Text('You hit me: ${snapshot.data} times');
          },
        ),
        RaisedButton(
          child: Text('Hit me'),
          onPressed: () {
            _bloc.counterEventSink.add(IncrementEvent());
          },
        )
      ],
    );
  }
}
```
In this example, pressing the ‘Hit me’ button will add an IncrementEvent to the CounterBloc. The BLoC will then increment the counter and add the new value to its state stream. The StreamBuilder widget listens to this stream and rebuilds whenever it receives a new value1.

Remember to always dispose of your BLoCs when they’re no longer needed to close their streams and prevent memory leaks1. In this example, you might add a dispose method to MyWidget that disposes of _bloc.

This is a simple example, but the BLoC pattern can be used to manage more complex state in larger applications1. I hope this helps you understand how to implement the BLoC pattern!
