"""
Custom blocks for the demo application.

This module demonstrates how to register custom blocks that will be
automatically added to STREAMFIELD_COMMON_BLOCKS.
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from sites_conformes.content_manager.registry import register_common_block


@register_common_block(label="Demo Custom Block", group="Demo Blocks")
class DemoCustomBlock(blocks.StructBlock):
    """
    A custom block to demonstrate the registry system.
    """

    title = blocks.CharBlock(required=True, help_text="Title for the custom block")
    content = blocks.RichTextBlock(
        required=False, help_text="Content of the custom block"
    )
    show_border = blocks.BooleanBlock(
        required=False, help_text="Show a border around the block"
    )

    class Meta:
        icon = "placeholder"
        template = "demo/blocks/demo_custom_block.html"


@register_common_block(
    name="featured_content",
    label="Featured Content",
    group="Demo Blocks",
)
class FeaturedContentBlock(blocks.StructBlock):
    """
    Another example of a custom registered block with explicit name.
    """

    headline = blocks.CharBlock(required=True)
    description = blocks.TextBlock(required=False)
    image = ImageChooserBlock(required=False)
    link = blocks.URLBlock(required=False)

    class Meta:
        icon = "pick"
        template = "demo/blocks/featured_content_block.html"


@register_common_block(
    name="coucou",
    label="Coucou",
    group="Coucou Blocks",
)
class CoucouBlock(blocks.StructBlock):
    """
    Another example of a custom registered block with explicit name.
    """

    headline = blocks.CharBlock(required=True)
    description = blocks.TextBlock(required=False)
    image = ImageChooserBlock(required=False)
    link = blocks.URLBlock(required=False)

    class Meta:
        icon = "pick"
        template = "demo/blocks/featured_content_block.html"
