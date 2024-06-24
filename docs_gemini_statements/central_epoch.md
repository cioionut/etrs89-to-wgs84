The concept of a central epoch exists in a Helmert transformation, but it's not directly tied to a specific reference frame like ETRF2014. Here's the breakdown:

**Central Epoch in Helmert Transformation:**

* A Helmert transformation is a method used to convert coordinates between different reference frames (like ETRF2014 and another).
* It accounts for shifts like translation, rotation, and scaling.
* The central epoch is a specific point in time associated with the defined Helmert transformation parameters. 

**Why is it important?**

The Earth's surface is constantly moving due to tectonic plate movements. This means the relationship between reference frames can change slightly over time.

* The central epoch tells you the time at which the Helmert transformation parameters were most accurate.
*  If you're using coordinates with a different time stamp, you might need to account for these changes for higher precision.

**Finding the Central Epoch:**

* The central epoch might be explicitly documented alongside the other Helmert transformation parameters (translation, rotation, scale).
* Software like PROJ (commonly used for coordinate transformations) uses a parameter called `t_epoch` to specify the central epoch [https://proj.org/en/9.3/tutorials/EUREF2019/exercises/helmert.html](https://proj.org/en/9.3/tutorials/EUREF2019/exercises/helmert.html). 

**In summary:**

The central epoch is a crucial piece of information for ensuring accurate coordinate transformations using the Helmert method. It signifies the specific time when the provided transformation parameters are most valid. 