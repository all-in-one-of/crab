import pymel.core as pm

from crab.utils import shapes
from . import config


# ------------------------------------------------------------------------------
def joint(description,
          side,
          parent=None,
          xform=None,
          match_to=None,
          radius=3):
    """
    Creates a joint, ensuring the right parenting and radius

    :param description: Descriptive section of the name
    :type description: str

    :param side: Tag for the location to be used during the name generation
    :type side: str

    :param parent: Optional parent to assign to the node
    :type parent: pm.nt.DagNode

    :param xform: Optional worldSpace matrix to apply to the object
    :type xform: pm.dt.Matrix

    :param match_to: Optional node to match in worldspace
    :type match_to: pm.nt.DagNode

    :param radius: Radius to assign to the joint
    :type radius: int

    :return: pm.nt.DependNode
    """
    # -- Joints always parent under whatever is selected, so
    # -- clear the selection
    pm.select(clear=True)

    # -- Create the joint
    new_joint = generic(
        'joint',
        config.SKELETON,
        description,
        side,
        parent=parent,
        xform=xform,
        match_to=match_to,
    )

    new_joint.jointOrientX.set(0)
    new_joint.jointOrientY.set(0)
    new_joint.jointOrientZ.set(0)

    if parent:
        new_joint.setMatrix(
            parent.getMatrix(worldSpace=True),
            worldSpace=True,
        )

    # -- If we're given a matrix utilise that
    if xform:
        new_joint.setMatrix(
            xform,
            worldSpace=True,
        )

    # -- Match the object to the target object if one
    # -- is given.
    if match_to:
        new_joint.setMatrix(
            match_to.getMatrix(worldSpace=True),
            worldSpace=True,
        )

    # -- Set the joint radius
    new_joint.radius.set(radius)

    # -- Clear the selection
    pm.select(clear=True)

    return new_joint


# ------------------------------------------------------------------------------
def control(description,
            side,
            parent=None,
            xform=None,
            match_to=None,
            shape=None,
            lock_list=None,
            hide_list=None,
            rotation_order=None):
    """
    Creates a control structure - which is a structure which conforms to the
    following hierarchy:

        ORG -> ZRO -> OFF -> CTL

    :param description: Descriptive section of the name
    :type description: str

    :param side: Tag for the location to be used during the name generation
    :type side: str

    :param parent: Optional parent to assign to the node
    :type parent: pm.nt.DagNode

    :param xform: Optional worldSpace matrix to apply to the object
    :type xform: pm.dt.Matrix

    :param match_to: Optional node to match in worldspace
    :type match_to: pm.nt.DagNode

    :param shape: Optional shape to apply to the node
    :type shape: name of shape or path

    :param lock_list: This is a list of attribute names you want to lock. This
        is only applied to the control.
    :type lock_list: A list of strings, or a string deliminated by ;

    :param hide_list: This is a list of attribute names you want to hide. This
        is only applied to the control.
    :type hide_list: A list of strings, or a string deliminated by ;

    :return: pm.nt.DependNode
    """
    prefixes = [
        config.ORG,
        config.ZERO,
        config.OFFSET,
        config.CONTROL,
    ]

    for prefix in prefixes:

        # -- Declare any specific options for this iteration
        options = dict()

        # -- Controls are the only items which have shapes
        if prefix == config.CONTROL:
            options['shape'] = shape

        parent = generic(
            'transform',
            prefix,
            description,
            side,
            parent=parent,
            xform=xform,
            match_to=match_to,
            **options
        )

    # -- Check if we need to convert lock or hide data
    if hide_list and not isinstance(hide_list, list):
        hide_list = hide_list.split(';')

    if lock_list and not isinstance(lock_list, list):
        lock_list = lock_list.split(';')

    if hide_list:
        for attr_to_hide in hide_list:
            if attr_to_hide:
                parent.attr(attr_to_hide).set(k=False)

    if lock_list:
        for attr_to_lock in lock_list:
            if attr_to_lock:
                parent.attr(attr_to_lock).lock()

    # -- Now expose the rotation order
    parent.rotateOrder.set(k=True)

    parent.rotateOrder.set(
        rotation_order or config.DEFAULT_CONTROL_ROTATION_ORDER
    )

    return parent


# ------------------------------------------------------------------------------
def guide(description,
          side,
          parent=None,
          xform=None,
          match_to=None,
          link_to=None,
          shape=None, ):
    """
    Creates a control structure - which is a structure which conforms to the
    following hierarchy:

        ORG -> ZRO -> OFF -> CTL

    :param description: Descriptive section of the name
    :type description: str

    :param side: Tag for the location to be used during the name generation
    :type side: str

    :param parent: Optional parent to assign to the node
    :type parent: pm.nt.DagNode

    :param xform: Optional worldSpace matrix to apply to the object
    :type xform: pm.dt.Matrix

    :param match_to: Optional node to match in worldspace
    :type match_to: pm.nt.DagNode

    :param shape: Optional shape to apply to the node
    :type shape: name of shape or path

    :param link_to: If given, an unselectable line is drawn between this
        guide control and the given transform.
    :type link_to: pm.nt.DagNode

    :return: pm.nt.DependNode
    """
    guide_node = generic(
        'transform',
        config.GUIDE,
        description,
        side,
        shape=shape or 'cube',
        parent=parent,
        xform=xform,
        match_to=match_to,
    )

    if link_to:
        curve = pm.curve(
            d=1,
            p=[
                [0, 0, 0],
                [0, 0, 0],
            ],
        )

        curve.setParent(guide_node)
        curve.inheritsTransform.set(False)

        # -- Make the curve unselectable
        curve.getShape().template.set(True)

        # -- Create the first cluster
        pm.select('%s.cv[0]' % curve.name())
        cls_root_handle, cls_root_xfo = pm.cluster()

        # -- Create the second cluster
        pm.select('%s.cv[1]' % curve.name())
        cls_target_handle, cls_target_xfo = pm.cluster()

        # -- Hide the clusters, as we do not want them
        # -- to be interactable
        cls_root_xfo.visibility.set(False)
        cls_target_xfo.visibility.set(False)

        # -- Ensure they're both children of the guide
        cls_root_xfo.setParent(guide_node)
        cls_target_xfo.setParent(guide_node)

        # -- Ensure the target is zero'd
        cls_target_xfo.setMatrix(pm.dt.Matrix())

        # -- Constrain the root to the linked object
        pm.parentConstraint(
            link_to,
            cls_root_xfo,
            maintainOffset=False,
        )

    # -- Set the guide specific colouring
    guide_node.useOutlinerColor.set(True)
    guide_node.outlinerColorR.set(config.GUIDE_COLOR[0] * (1.0 / 255))
    guide_node.outlinerColorG.set(config.GUIDE_COLOR[1] * (1.0 / 255))
    guide_node.outlinerColorB.set(config.GUIDE_COLOR[2] * (1.0 / 255))

    for guide_shape in guide_node.getShapes():
        # -- Set the display colour
        guide_shape.overrideEnabled.set(True)
        guide_shape.overrideRGBColors.set(True)

        guide_shape.overrideColorR.set(config.GUIDE_COLOR[0] * (1.0 / 255))
        guide_shape.overrideColorG.set(config.GUIDE_COLOR[1] * (1.0 / 255))
        guide_shape.overrideColorB.set(config.GUIDE_COLOR[2] * (1.0 / 255))

    return guide_node


# ------------------------------------------------------------------------------
def org(description, side, parent=None):
    """
    Creates a simple org node

    :param description: Descriptive section of the name
    :type description: str

    :param side: Tag for the location to be used during the name generation
    :type side: str

    :param parent: Optional parent to assign to the node
    :type parent: pm.nt.DagNode

    """
    return generic(
        prefix=config.ORG,
        node_type='transform',
        description=description,
        side=side,
        parent=parent,
        match_to=parent,
    )


# ------------------------------------------------------------------------------
def generic(node_type,
            prefix,
            description,
            side,
            parent=None,
            xform=None,
            match_to=None,
            shape=None):
    """
    Convenience function for creating a node, generating the name using
    the unique name method and giving the ability to assign the parent and
    transform.

    :param node_type: Type of node to create, such as 'transform'
    :type node_type: str

    :param prefix: Prefix to assign to the node name
    :type prefix: str

    :param description: Descriptive section of the name
    :type description: str

    :param side: Tag for the location to be used during the name generation
    :type side: str

    :param parent: Optional parent to assign to the node
    :type parent: pm.nt.DagNode

    :param xform: Optional worldSpace matrix to apply to the object
    :type xform: pm.dt.Matrix

    :param match_to: Optional node to match in worldspace
    :type match_to: pm.nt.DagNode

    :param shape: Optional shape to apply to the node
    :type shape: name of shape or path

    :return: pm.nt.DependNode
    """
    # -- Create the node
    node = pm.createNode(node_type)

    # -- Name it based on our naming convention
    node.rename(
        config.name(
            prefix=prefix,
            description=description,
            side=side,
        ),
    )

    # -- If we're given a matrix utilise that
    if xform:
        node.setMatrix(
            xform,
            worldSpace=True,
        )

    # -- Match the object to the target object if one
    # -- is given.
    if match_to:
        node.setMatrix(
            match_to.getMatrix(worldSpace=True),
            worldSpace=True,
        )

    # -- Parent the node if we're given a parent
    if parent:
        node.setParent(parent)

    if shape:
        shapes.apply(node, shape)

    return node
