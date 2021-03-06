/*#############################################################################
# Copyright Kitware Inc. and Contributors
# Distributed under the Apache License, 2.0 (apache.org/licenses/LICENSE-2.0)
# See accompanying Copyright.txt and LICENSE files for details
#############################################################################*/

<template>
  <div class='edit-workingset'>
    <div class='main ma-2'>
      <v-layout>
        <v-flex>
          <v-text-field
            class="input"
            name="Name"
            label="Name"
            hint="A unique name for the working set"
            v-model="name"
          ></v-text-field>
        </v-flex>
      </v-layout>
      <v-layout>
        <v-flex>
          <v-select
            :items="filters"
            v-model="filterId"
            label="Filter"
            item-text="name"
            item-value='_id'
          ></v-select>
        </v-flex>
      </v-layout>
      <v-layout>
        <transition name='fade'>
          <v-flex xs12 class='datasets' v-if="datasets.length">
            <div class='body-2'>Datasets</div>
            <transition-group name="slide-fade-group" tag="div">
              <div v-for="dataset in filteredDatasets" :key="dataset._id">
                <v-tooltip top open-delay="1000">
                  <span>{{dataset.name}}</span>
                  <v-chip slot="activator" outline close color="primary" class='dataset'
                    @input="removeDataset(dataset)"
                    @mouseenter.native="setSelectedDataset(dataset)"
                    @mouseleave.native="setSelectedDataset(null)"
                  ><span>{{dataset.name}}</span></v-chip>
                </v-tooltip>
              </div>
            </transition-group>
          </v-flex>
        </transition>
      </v-layout>
    </div>
    <v-container grid-list-lg class="py-2">
      <v-layout>
        <v-flex xs3>
          <v-btn block depressed color='error'
            :disabled="!editingWorkingSet._id"
            @click="deleteRecord">
            <v-icon>delete</v-icon>
          </v-btn>
        </v-flex>
        <v-flex xs4>
          <v-btn block outline color='error' @click="exit">
            Cancel
          </v-btn>
        </v-flex>
        <v-flex xs5>
          <v-btn block depressed color='primary'
            :disabled="!name"
            @click="save">
            Save
            <v-icon class='ml-1'>save</v-icon>
          </v-btn>
        </v-flex>
      </v-layout>
    </v-container>
  </div>
</template>

<script>
import { mapState, mapMutations } from "vuex";

import {
  loadDatasetByWorkingSetId,
  loadDatasetByFilterConditions
} from "../utils/loadDataset";
import DateRangeControl from "./DateRangeControl";

export default {
  name: "EditWorkingSet",
  components: {
    DateRangeControl
  },
  props: {},
  data() {
    return {
      portal: {
        name: "title",
        text: "Edit Working set"
      },
      name: null,
      filterId: null
    };
  },
  computed: {
    regionFilters() {
      return this.workingSet.filters.filter(filter => filter.type === "region");
    },
    dateRangeFilters() {
      return this.workingSet.filters.filter(
        filter => filter.type === "daterange"
      );
    },
    undoSnackbar: {
      get: function() {
        return !!this.undoMessage;
      },
      set: function(value) {
        if (!value) {
          this.undoMessage = null;
        }
      }
    },
    filteredDatasets() {
      if (!this.datasets) {
        return;
      } else {
        return this.datasets.filter(dataset => !dataset.name.endsWith(".tar"));
      }
    },
    ...mapState(["filters"]),
    ...mapState("workingSet", [
      "editingWorkingSet",
      "datasets",
      "selectedDataset"
    ])
  },
  watch: {
    filterId(filterId) {
      if (!this.initialized) {
        return;
      }
      if (!filterId) {
        return;
      }
      this.loadDatasets(filterId);
    }
  },
  created() {
    this.name = this.editingWorkingSet.name;
    this.filterId = this.editingWorkingSet.filterId;
    if (this.filterId && this.editingWorkingSet.datasetIds.length === 0) {
      this.loadDatasets(this.filterId);
    } else {
      if (this.editingWorkingSet._id) {
        loadDatasetByWorkingSetId(this.editingWorkingSet._id).then(datasets => {
          this.initialized = true;
          this.$store.commit("workingSet/setDatasets", datasets);
        });
      } else {
        this.initialized = true;
        this.$store.commit("workingSet/setDatasets", []);
      }
    }
  },
  methods: {
    exit() {
      this.$store.commit("workingSet/setDatasets", []);
      this.$store.commit("workingSet/setEditingWorkingSet", null);
    },
    save() {
      this.$store
        .dispatch("saveWorkingSet", {
          _id: this.editingWorkingSet._id,
          name: this.name,
          filterId: this.filterId,
          datasetIds: this.datasets.map(dataset => dataset._id)
        })
        .then(workingSet => {
          Object.assign(this.editingWorkingSet, workingSet);
          this.exit();
        });
    },
    deleteRecord() {
      this.$store
        .dispatch("deleteWorkingSet", this.editingWorkingSet)
        .then(() => {
          this.exit();
        });
    },
    loadDatasets(filterId) {
      this.$store.commit("workingSet/setDatasets", []);
      var filter = this.filters.filter(filter => filter._id === filterId)[0];
      loadDatasetByFilterConditions(filter.conditions).then(datasets => {
        this.$store.commit("workingSet/setDatasets", datasets);
      });
    },
    removeDataset(dataset) {
      this.datasets.splice(this.datasets.indexOf(dataset), 1);
      this.setSelectedDataset(null);
    },
    ...mapMutations("workingSet", ["setSelectedDataset"])
  }
};
</script>

<style lang="scss" scoped>
.edit-workingset {
  display: flex;
  flex-direction: column;

  .main {
    flex: 1;
    display: flex;
    flex-direction: column;

    .datasets,
    .filters {
      flex: 1;
    }

    .datasets .dataset {
      width: 100%;
    }
  }
}

// overwrite
.v-expansion-panel {
  box-shadow: none;
}
</style>

<style lang="scss">
.datasets {
  .v-chip {
    .v-chip__content {
      span {
        width: calc(100% - 20px);
        overflow-x: hidden;
      }
    }
  }
}
</style>
