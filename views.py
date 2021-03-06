from webengine.utils.decorators import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from webengine.utils.log import logger

from team.models import Person
from workflow.forms import *
from workflow.models import *

@render(view='index')
def index(request):
    return {}

@render(view='workflowinstance_new')
def workflowinstance_new(request):
    if request.method == 'POST':
        form = WorkflowInstanceNewForm(request, data=request.POST)
        if form.is_valid():
            workflow_id = form.cleaned_data['workflow']
            persons = Person.objects.filter(django_user=request.user.id)
            if not len(persons):
                return {"form" : form, "status" : "KO", "error" : "Your django user is not attached to a Team person"}
            if len(Workflow.objects.filter(id=workflow_id)[0].leaders.filter(id=persons[0].id)):
                new_workflowinstance=WorkflowInstance(workflow_id=form.cleaned_data['workflow'], version = form.cleaned_data['version'])
                new_workflowinstance.save()
                categories = WorkflowCategory.objects.filter(workflow=workflow_id)
                for category in categories:
                    items = Item.objects.filter(workflow_category=category.id)
                    for item in items:
                        rt = WorkflowInstanceItems(validation=None, item_id = item.id, workflowinstance_id=new_workflowinstance.id)
                        rt.save()
                return HttpResponseRedirect(reverse('workflow-workflowinstance-show', args=[new_workflowinstance.id]))
            else:
                return {"status" : "KO", "error" : "You are not leader on this workflow"}
        else:
            return {"status" : "KO", "error" : str(form.errors)}
    else:
        form = WorkflowInstanceNewForm(request)

    return {'form' : form, "status" : "NEW"}

@render(view='workflowinstance_list')
def workflowinstance_list(request):
    workflows = Workflow.objects.all()
    ret = {'workflows' : []}
    display = { 'mine' : 'mine', 'all' : 'all', 'successful' : 'successful', 'failed' : 'failed', 'untaken' : 'untaken', 'taken' : 'taken' }
    for workflow in workflows:
        ret['workflows'] += [{'name' : workflow, 'workflowinstances' : WorkflowInstance.objects.filter(workflow=workflow)}]
        ret.update({'display' : display})
    return ret

@render(output='json')
def check_state_before_change(request, item_id, category_id):
    """ Check if @item_id@ or @category_id@ have changed before change anything
    """
    if int(item_id):
        item = WorkflowInstanceItems.objects.filter(id=item_id)[0]
        return {"assigned_to" : item.assigned_to_id or "None",\
                "validation" : item.validation_id == 1 and "OK" or item.validation_id == 2 and "KO" or "None",\
                "item_id" : item_id}
    else:
        return {"category_id" : category_id}

def _fill_container(dict_to_fill, which_display):
    for category in dict_to_fill[which_display]:
        dict_to_fill[which_display][category]['workflowinstanceitems'] = dict_to_fill[which_display][category]['workflowinstanceitems'].values()
    return {'categories' : len(dict_to_fill[which_display]) and dict_to_fill[which_display].values() or None}

@render(view='workflowinstance_show')
def workflowinstance_show(request, workflowinstance_id, which_display):
    workflowinstanceitems = WorkflowInstanceItems.objects.filter(workflowinstance=workflowinstance_id)
    person_id = Person.objects.filter(django_user=request.user.id)[0].id

    display = { 'mine' : 'mine', 'all' : 'all', 'successful' : 'successful', 'failed' : 'failed', 'untaken' : 'untaken', 'taken' : 'taken' }
    counter = {'Total' : len(workflowinstanceitems), 'Success' : 0, 'Failed' : 0, 'Taken' : 0, 'Free' : 0, 'NotSolved' : 0, 'Mine' : 0}
    container = {'mine' : dict(),
                'successful' : dict(),
                'failed' : dict(),
                'untaken' : dict(),
                'taken' : dict(),
                'all' : dict()
                }

    if not which_display in container.keys():
        which_display = "all"
    for workflowinstanceitem in workflowinstanceitems:
        category_id=workflowinstanceitem.item.workflow_category.id
        container["all"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
        container["all"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
        if workflowinstanceitem.assigned_to_id == person_id:
            container["mine"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
            container["mine"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
            counter['Mine'] += 1
        if not workflowinstanceitem.validation_id == None:
            if workflowinstanceitem.validation_id == 1:
                container["successful"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
                container["successful"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
                counter['Success'] += 1
            elif workflowinstanceitem.validation_id == 2:
                container["failed"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
                container["failed"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
                counter['Failed'] += 1
        else:
            counter['NotSolved'] += 1
        if workflowinstanceitem.assigned_to == None:
            container["untaken"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
            container["untaken"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
            counter['Free'] += 1
        if not workflowinstanceitem.assigned_to == None:
            container["taken"].setdefault(category_id, {'id' : category_id, 'name' : workflowinstanceitem.item.workflow_category.name, 'workflowinstanceitems' : {}})
            container["taken"][category_id]['workflowinstanceitems'][workflowinstanceitem.id] = workflowinstanceitem
            counter['Taken'] += 1

    return_d = {}
    return_d.update({'validations' : Validation.objects.all(), 'categories' : container["all"].values(), \
            'workflowinstance' : WorkflowInstance.objects.filter(id=workflowinstance_id)[0]})
    return_d.update({'display' : display, 'counter' : counter})
    return_d.update(_fill_container(container, which_display))
    return return_d

def workflowinstance_delete(request, workflowinstance_id):
    WorkflowInstance.objects.filter(id=workflowinstance_id).delete()
    return HttpResponseRedirect(reverse('workflow-workflowinstance-list'))

def workflowinstanceitem_assign_to_person(workflowinstanceitem, person):
    """ Change item assignation and save into db """
    workflowinstanceitem.assigned_to = person
    workflowinstanceitem.save()

@render(output='json')
def workflowinstanceitem_take(request, workflowinstanceitem_id):
    """ Output JSON for AJAX interaction
        Set owner on @workflowinstanceitem_id@
        Return @workflowinstanceitem_id@
    """
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    person = Person.objects.filter(django_user=request.user.id)[0]
    workflowinstanceitem_assign_to_person(workflowinstanceitem, person)
    return {"item_id" : workflowinstanceitem_id, "assigned_to_firstname" : str(person.firstname), "assigned_to_lastname" : str(person.lastname), "assigned_to" : person.id or "None"}

@render(output='json')
def workflowinstanceitem_untake(request, workflowinstanceitem_id):
    """ Output JSON for AJAX interaction
        Reset owner one @workflowinstanceitem_id@
        Return @workflowinstanceitem_id@
    """
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    workflowinstanceitem.assigned_to = None
    workflowinstanceitem.save()
    return {"item_id" : workflowinstanceitem_id, "assigned_to" : workflowinstanceitem.assigned_to_id or "None"}

@render(output='json')
def workflowinstance_take_category(request, workflowinstance_id, category_id):
    """ Output JSON for AJAX interaction
        Set owner on concerned items
        Return the category_id of item concerned and owner's lastname and firstname
    """
    items = WorkflowInstanceItems.objects.filter(workflowinstance__id=workflowinstance_id)
    person = Person.objects.filter(django_user=request.user.id)[0]
    for item in items:
        if item.item.workflow_category.id == int(category_id) and not item.assigned_to_id:
            workflowinstanceitem_assign_to_person(item, person)
    return {"category_id" : category_id, "assigned_to_firstname" : str(person.firstname), "assigned_to_lastname" : str(person.lastname), "assigned_to" : person.id}

@render(output='json')
def workflowinstance_untake_category(request, workflowinstance_id, category_id):
    """ Output JSON for AJAX interaction
        Reset owner on concerned items
        Return the category_id of item
    """
    items = WorkflowInstanceItems.objects.filter(workflowinstance__id=workflowinstance_id)
    person = Person.objects.filter(django_user=request.user.id)[0]
    for item in items:
        if item.item.workflow_category.id == int(category_id) and item.assigned_to_id == person.id:
            workflowinstanceitem_assign_to_person(item, None)
    return {"category_id" : category_id, "person_id" : person.id}

@render(output='json')
def workflowinstanceitem_validate(request, workflowinstanceitem_id, validation_label):
    """ Output JSON for AJAX interaction
        Change item state: Validate/Invalidate
        Return @workflowinstanceitem_id@ which is the item id
    """
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    workflowinstanceitem.validation_id = validation_label == "OK" and 1 or 2
    workflowinstanceitem.save()
    return {"item_id" : workflowinstanceitem_id}

@render(output='json')
def workflowinstanceitem_no_state(request, workflowinstanceitem_id):
    """ Reset item state
        Return @item_id@
    """
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    workflowinstanceitem.validation_id = None
    workflowinstanceitem.save()
    return {"item_id" : workflowinstanceitem_id}

@render(view='workflowinstanceitem_show')
def workflowinstanceitem_show(request, workflowinstanceitem_id):
    """ Create form for comments
        Create form for edit details
        Get information about current item @workflowinstanceitem_id@

        Return dictionnary with all of that
    """
    return_d = {}
    return_d.update(workflowinstanceitem_comments(request, workflowinstanceitem_id))
    return_d.update(workflowinstanceitem_details(request, workflowinstanceitem_id))
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    if workflowinstanceitem.item.details:
        workflowinstanceitem.item.details = workflowinstanceitem.item.details
    else:
        workflowinstanceitem.item.details = []
    comments = CommentInstanceItem.objects.filter(item=workflowinstanceitem_id)
    return_d.update({'workflowinstanceitem' : workflowinstanceitem, 'validations' : Validation.objects.all()})
    return_d.update({'from_item_details' : 'from_item_details', 'comments' : comments, "all" : "all"})
    return return_d

def workflowinstanceitem_comments(request, workflowinstanceitem_id):
    """ Return form for comments on specific item """
    if request.method == 'POST':
        person = Person.objects.filter(django_user=request.user.id)[0]
        form = CommentItemNewForm(request, data=request.POST)
        if form.is_valid():
            comment = CommentInstanceItem(comments=form.cleaned_data['comments'], item_id=workflowinstanceitem_id, person=person)
            comment.save()
            form = CommentItemNewForm(request)
            return {'status_comment' : 'OK', 'form_comment' : form}
        else:
            return {'status_comment' : 'KO', 'error' : str(form.errors), 'form_comment' : form}
    else:
        form = CommentItemNewForm(request)
    return {'form_comment' : form}

def workflowinstanceitem_details(request, workflowinstanceitem_id):
    """ Return form for details on specific item """
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    initial_value = workflowinstanceitem.item.details
    if request.method == 'POST' and "_post" in request.POST:
        form = DetailItemForm(request, initialValue='', data=request.POST)
        if form.is_valid():
            workflowcategory = WorkflowCategory.objects.filter(id=workflowinstanceitem.item.workflow_category_id)[0]
            detail = Item(id=workflowinstanceitem.item.id, workflow_category=workflowcategory, \
                    label=workflowinstanceitem.item.label, details=form.cleaned_data['details'])
            detail.save()
            form = DetailItemForm(request, initialValue=form.cleaned_data['details'])
            return {'status_detail' : 'OK', 'form_detail' : form}
        else:
            return {'status_detail' : 'KO', 'error' : str(form.errors), 'form_detail' : form}
    elif "_reset" in request.POST:
        workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
        workflowcategory = WorkflowCategory.objects.filter(id=workflowinstanceitem.item.workflow_category_id)[0]
        detail = Item(id=workflowinstanceitem.item.id, workflow_category=workflowcategory, \
                    label=workflowinstanceitem.item.label, details='')
        detail.save()
        form = DetailItemForm(request, initialValue='')
        return {'form_detail' : form}
    else:
        form = DetailItemForm(request, initial_value)
    return {'form_detail' : form}

def item_create(request, workflowinstanceitem_id):
    workflowinstanceitem = WorkflowInstanceItems.objects.filter(id=workflowinstanceitem_id)[0]
    workflowinstanceitem.save()
    return HttpResponseRedirect(reverse('workflow-workflowinstance-show', args=[workflowinstanceitem.workflowinstance.id]))

@render(view='item_new')
def item_new(request):
    if request.method == 'POST':
        form = ItemNewForm(request, data=request.POST)
        if form.is_valid():
            workflowcategory_id = int(form.cleaned_data['category'])
            workflowcategory = WorkflowCategory.objects.filter(id=workflowcategory_id)[0]
            workflow = workflowcategory.workflow

            persons = Person.objects.filter(django_user=request.user.id)
            if not len(persons):
                return {"form" : form, "status" : "KO", "error" : "Your django user is not attached to a Team person"}

            if len(Workflow.objects.filter(id=workflow.id)[0].leaders.filter(id=persons[0].id)):

                for label in form.cleaned_data['items'].splitlines():
                    label = label.strip()
                    if not label:
                        continue
                    item=Item(workflow_category_id=workflowcategory_id, label=label)
                    item.save()
                return {"status" : "OK"}
            else:
                return {"status" : "KO", "error" : "You are not leader on this workflow"}

        else:
            return {"status" : "KO", "error" : str(form.errors)}
    else:
        form = ItemNewForm(request)

    return {'form' : form, "status" : "NEW"}
